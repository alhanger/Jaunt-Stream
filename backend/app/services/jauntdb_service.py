import sqlite3
from pathlib import Path
import logging
from typing import Dict, List

class JauntDBService:
    def __init__(self, db_dir: str = "data"):
        
        self.data_dir = Path(db_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.data_dir / "jauntee_archive.db"
        self.log_path = self.data_dir / "db_service.log"

        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_path),
                logging.StreamHandler()
            ]
        )

    def get_years(self, order='DESC') -> List[Dict]:
        c = self.create_cursor(True)
        
        years = []
        result = c.execute(f'''
                SELECT date
                FROM shows
                ORDER BY date {order};
                  ''').fetchall()
        
        print(f'Row keys: {result.keys()}')
        for row in result:
            years.append(row)
            
        
        return result
        
    def load_show_data(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        result = c.execute('''
                           SELECT shows.id, tracks.name AS track_name 
                           FROM shows 
                           LEFT JOIN tracks ON shows.id = tracks.show_id 
                           ORDER BY shows.id, tracks.track_number;
                           ''')

        shows_data = []
        current_show = None
        
        for row in result:
            if current_show is None or current_show['id'] != row ['id']:
                if current_show is not None:
                    shows_data.append(current_show)
                current_show = {
                    'id': row['id'],
                    'tracks': []
                }

            if row['track_name']:
                current_show['tracks'].append({
                    'name': row['track_name']
                })

        if current_show is not None:
            shows_data.append(current_show)

        return shows_data
    
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
    
    def create_cursor(self, row=False):
        conn = sqlite3.connect(self.db_path)
        
        if row == True:
            conn.row_factory = sqlite3.Row
        
        c = conn.cursor()
        
        return c