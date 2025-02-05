import internetarchive as ia
import sqlite3
from datetime import datetime
import logging
import json
from pathlib import Path
import time
from typing import Dict, List, Optional
import os

class ArchiveScraper:
    def __init__(self, db_dir: str = "data"):
        """
        Initialize scraper with custom database directory
        
        Args:
            db_dir (str): Directory to store the database and logs
        """
        # Create data directory if it doesn't exist
        self.data_dir = Path(db_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Set database and log paths
        self.db_path = self.data_dir / "jauntee_archive.db"
        self.log_path = self.data_dir / "scraper.log"
        
        self.setup_logging()
        self.setup_database()

    def setup_logging(self):
        """Configure logging to both file and console"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_path),
                logging.StreamHandler()
            ]
        )

    def setup_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Shows table
        c.execute('''
            CREATE TABLE IF NOT EXISTS shows (
                id TEXT PRIMARY KEY,
                date TEXT,
                venue TEXT,
                location TEXT,
                description TEXT,
                source TEXT,
                metadata TEXT,
                last_updated TEXT
            )
        ''')

        # Tracks table with additional indexes
        c.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                id TEXT PRIMARY KEY,
                show_id TEXT,
                name TEXT,
                duration INTEGER,
                size INTEGER,
                format TEXT,
                bitrate TEXT,
                track_number INTEGER,
                FOREIGN KEY (show_id) REFERENCES shows (id)
            )
        ''')
        
        # Create indexes for common queries
        c.execute('CREATE INDEX IF NOT EXISTS idx_shows_date ON shows(date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_tracks_name ON tracks(name)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_tracks_show_id ON tracks(show_id)')

        conn.commit()
        conn.close()

    def parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse date string from Archive.org metadata"""
        if not date_str:
            return None

        date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%Y%m%d']
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None

    def clean_track_name(self, filename: str) -> str:
        """Clean track name from filename"""
        name = filename.rsplit('.', 1)[0]
        if name[0].isdigit():
            name = name.split(' ', 1)[1]
        return name

    def scrape_shows(self):
        """Scrape all shows from Archive.org"""
        logging.info("Starting show scraping process...")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        query = "collection:TheJauntee"
        print(f"Scraping all J-Boy shows")
        search = ia.search_items(query, params={'rows': 1000})

        count = 0
        
        for result in search:
            try:
                count += 1
                print(f"Searching show #{count}")
                item = ia.get_item(result['identifier'])
                
                show_data = {
                    'id': item.identifier,
                    'date': self.parse_date(item.metadata.get('date')),
                    'venue': item.metadata.get('venue'),
                    'location': item.metadata.get('coverage'),
                    'description': item.metadata.get('description'),
                    'source': item.metadata.get('source'),
                    'metadata': json.dumps(item.metadata)
                }
                
                c.execute('''
                    INSERT OR REPLACE INTO shows 
                    (id, date, venue, location, description, source, metadata, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    show_data['id'],
                    show_data['date'],
                    show_data['venue'],
                    show_data['location'],
                    show_data['description'],
                    show_data['source'],
                    show_data['metadata'],
                    datetime.now().isoformat()
                ))

                track_number = 1
                for file in item.get_files():
                    if file.format == 'VBR MP3':
                        track_data = {
                            'id': f"{show_data['id']}/{file.name}",
                            'show_id': show_data['id'],
                            'name': self.clean_track_name(file.name),
                            'duration': file.length if file.length else None,
                            'size': file.size,
                            'format': file.format,
                            'bitrate': file.bitrate,
                            'track_number': track_number
                        }
                        
                        c.execute('''
                            INSERT OR REPLACE INTO tracks 
                            (id, show_id, name, duration, size, format, bitrate, track_number)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            track_data['id'],
                            track_data['show_id'],
                            track_data['name'],
                            track_data['duration'],
                            track_data['size'],
                            track_data['format'],
                            track_data['bitrate'],
                            track_data['track_number']
                        ))
                        
                        track_number += 1

                conn.commit()
                logging.info(f"Processed show: {show_data['id']}")
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"Error processing show {result['identifier']}: {str(e)}")
                continue

        conn.close()
        logging.info("Completed show scraping process")

    def get_stats(self):
        """Get statistics about the scraped data"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        stats = {
            'total_shows': c.execute('SELECT COUNT(*) FROM shows').fetchone()[0],
            'total_tracks': c.execute('SELECT COUNT(*) FROM tracks').fetchone()[0],
            'years_covered': c.execute(
                'SELECT MIN(substr(date,1,4)), MAX(substr(date,1,4)) FROM shows WHERE date IS NOT NULL'
            ).fetchone(),
            'total_duration': c.execute('SELECT SUM(duration) FROM tracks WHERE duration IS NOT NULL').fetchone()[0]
        }
        
        conn.close()
        return stats

    def query_shows_by_year(self, year: int) -> List[Dict]:
        """Get all shows from a specific year"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # This enables column name access
        c = conn.cursor()
        
        shows = c.execute('''
            SELECT * FROM shows 
            WHERE date LIKE ?
            ORDER BY date ASC
        ''', (f'{year}%',)).fetchall()
        
        result = [{key: show[key] for key in show.keys()} for show in shows]
        conn.close()
        return result

    def search_tracks(self, song_name: str) -> List[Dict]:
        """Search for tracks by name"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        results = c.execute('''
            SELECT t.*, s.date, s.venue, s.location
            FROM tracks t
            JOIN shows s ON t.show_id = s.id
            WHERE t.name LIKE ?
            ORDER BY s.date DESC
        ''', (f'%{song_name}%',)).fetchall()
        
        tracks = [{key: row[key] for key in row.keys()} for row in results]
        conn.close()
        return tracks

    def get_show_details(self, show_id: str) -> Dict:
        """Get detailed information about a specific show including its tracks"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        show = c.execute('SELECT * FROM shows WHERE id = ?', (show_id,)).fetchone()
        if not show:
            return None
            
        tracks = c.execute('''
            SELECT * FROM tracks 
            WHERE show_id = ? 
            ORDER BY track_number
        ''', (show_id,)).fetchall()
        
        result = {
            'show': {key: show[key] for key in show.keys()},
            'tracks': [{key: track[key] for key in track.keys()} for track in tracks]
        }
        
        conn.close()
        return result

    def get_venue_stats(self) -> List[Dict]:
        """Get statistics about performances at different venues"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        stats = c.execute('''
            SELECT 
                venue,
                COUNT(*) as show_count,
                MIN(date) as first_show,
                MAX(date) as last_show
            FROM shows
            WHERE venue IS NOT NULL
            GROUP BY venue
            ORDER BY show_count DESC
        ''').fetchall()
        
        result = [{
            'venue': row[0],
            'show_count': row[1],
            'first_show': row[2],
            'last_show': row[3]
        } for row in stats]
        
        conn.close()
        return result

def main():
    # Use a custom data directory
    # data_dir = os.path.join(os.path.expanduser('~'), 'jaunt-data')
    data_dir = "/Users/alhanger/Documents/Personal/The Jauntee Web App/jauntee-music-stream/jaunt-data"
    scraper = ArchiveScraper(data_dir)
    
    # Scrape data
    scraper.scrape_shows()
    
    # Print statistics
    stats = scraper.get_stats()
    logging.info("Scraping completed. Statistics:")
    logging.info(f"Total shows: {stats['total_shows']}")
    logging.info(f"Total tracks: {stats['total_tracks']}")
    logging.info(f"Years covered: {stats['years_covered'][0]} - {stats['years_covered'][1]}")
    logging.info(f"Total duration: {stats['total_duration']} seconds")
    
    # Example queries
    logging.info("\nExample Queries:")
    
    # Get shows from 2023
    shows_2023 = scraper.query_shows_by_year(2023)
    logging.info(f"\nShows from 2023: {len(shows_2023)}")
    
    # Search for a specific song
    song_results = scraper.search_tracks("Scarlet Begonias")
    logging.info(f"\nVersions of Scarlet Begonias: {len(song_results)}")
    
    # Get venue statistics
    venue_stats = scraper.get_venue_stats()
    logging.info("\nTop venues by show count:")
    for venue in venue_stats[:5]:
        logging.info(f"{venue['venue']}: {venue['show_count']} shows")

if __name__ == "__main__":
    main()