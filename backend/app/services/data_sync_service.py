import internetarchive as ia
import sqlite3
from datetime import datetime
import logging
import json
from pathlib import Path
import time
from typing import Optional
import os
import re
import csv

# TODO: write script to strip location names from venues and add them as separate columns
# TODO: move DB setup and DB-specific functionality to separate class

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
        self.log_path = self.data_dir / "track_scraper.log"
        
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
                    # File Formats: VBR MP3, Flac, 
                    if file.format == 'VBR MP3':
                        track_data = {
                            'id': f"{show_data['id']}/{file.name}",
                            'show_id': show_data['id'],
                            'name': self.clean_track_name(file.title),
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

    def tracks_csv(self):
        logging.info("Writing tracks to CSV")
        # Open CSV file with proper headers
        with open('jauntee_tracks.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['title'])
            writer.writeheader()
        
            query = "collection:TheJauntee"
            search = ia.search_items(query, params={'rows': 1000})
        
            for result in search:
                try:
                    item = ia.get_item(result['identifier'])
                    
                    for file in item.get_files():
                        if hasattr(file, 'title') and (file.format == 'VBR MP3' or file.format == 'Flac'):
                            logging.info(f"Writing {file.title}")
                            writer.writerow({
                                'title': file.title
                            })
                        
                except Exception as e:
                    print(f"Error processing {result['identifier']}: {str(e)}")
    
    def scrape_tracks(self):
        """Scrape all unique track names and write to DB"""
        logging.info("Starting track scraping process...")    

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        query = "collection:TheJauntee AND year:2011"
        print(f"Scraping all J-Boy shows")
        search = ia.search_items(query, params={'rows': 1000})

        for result in search:
            try:
                item = ia.get_item(result['identifier'])

                last_track = ''
                
                for file in item.get_files():
                    if hasattr(file, 'title'):
                        track_lowered = file.title.lower()
                        track = ArchiveScraper.sanitize_track(file.title)
                        if (file.format == 'VBR MP3' or file.format == 'Flac') and (track_lowered != last_track):
                            last_track = track_lowered
                            track_data = {
                                'title': track
                            }

                            c.execute('''
                                    INSERT OR REPLACE INTO track_titles
                                    (title)
                                    VALUES (?)
                                    ''', (
                                        track_data['title'],
                                    ))
                            
                            logging.info(f'Processed {track_data['title']}')

                conn.commit()
                time.sleep(1)

            except Exception as e:
                logging.error(f"Error processing show {result['identifier']}: {str(e)}")
                continue

        conn.close()
        logging.info("Completed track scraping process")
    
    def sanitize_track(title: str) -> str:
        # Remove arrows
        title = re.sub(r'\s*->\s*', ' ', title)
        title = re.sub(r'\s*>\s*', ' ', title)
    
        # Remove track numbers at start (e.g., "01. ", "1-", "1 ")
        title = re.sub(r'^\d+[\s\.-]+', '', title)
    
        # Remove show identifier pattern (e.g., "jauntee2011-12-03s2t06")
        title = re.sub(r'^jauntee\d{4}-\d{2}-\d{2}s\d+t\d+', '', title)
    
        # Remove specific characters
        title = title.replace('_', ' ')
        title = title.replace('^', '')
        title = title.replace('*', '')
        title = title.replace('+', '')
        title = title.replace('$', '')
        title = title.replace('-', '')
        title = title.replace('@', '')
        title = title.replace('#', '')
    
        # Clean up whitespace
        title = re.sub(r'\s+', ' ', title)
    
        return title.strip()

def main():
    # Use a custom data directory
    # data_dir = os.path.join(os.path.expanduser('~'), 'jaunt-data')
    data_dir = "/Users/alhanger/Documents/Personal/The Jauntee Web App/jauntee-music-stream/jaunt-data"
    db_url = "sqlite:/Users/alhanger/Documents/Personal/The Jauntee Web App/jauntee-music-stream/jaunt-data/jauntee_archive.db"
    scraper = ArchiveScraper(data_dir)
    scraper.load_show_data(db_url)
    
    # ArchiveScraper.scrape_shows(scraper)

if __name__ == "__main__":
    main()