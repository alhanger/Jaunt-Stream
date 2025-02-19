# app/services/archive.py
import internetarchive as ia
from typing import List, Dict, Optional
from datetime import datetime
import logging
from ..core.config import get_settings

class ArchiveService:
    def __init__(self):
        self.collection = "TheJauntee"  # The collection identifier for The Jauntee
        self.settings = get_settings()
        
    async def search_shows(self, year: Optional[int] = None) -> List[Dict]:
        """
        Search for The Jauntee shows, optionally filtered by year
        """
        query = f"collection:{self.collection}"
        if year:
            query += f" AND year:{year}"
            
        try:
            search_results = ia.search_items(query)
            shows = []
            
            for result in search_results:
                # Get detailed metadata for each show
                item = ia.get_item(result['identifier'])
                
                # Parse and format show data
                show_data = {
                    'id': item.identifier,
                    'date': self._parse_date(item.metadata.get('date')),
                    'venue': item.metadata.get('venue'),
                    'location': item.metadata.get('coverage'),
                    'description': item.metadata.get('description'),
                    'source': item.metadata.get('source'),
                    'tracks': self._parse_tracks(item)
                }
                shows.append(show_data)
                
            return shows
            
        except Exception as e:
            logging.error(f"Error searching shows: {e}")
            raise
            
    def _parse_tracks(self, item) -> List[Dict]:
        """
        Parse track information from an Archive.org item
        """
        tracks = []
        files = item.get_files()
        
        for file in files:
            if file.format == 'VBR MP3':
                track_data = {
                    'id': file.name,
                    'name': self._clean_track_name(file.name),
                    'duration': file.length,
                    'format': file.format,
                    'size': file.size,
                    'bitrate': file.bitrate,
                    'url': f"https://archive.org/download/{item.identifier}/{file.name}"
                }
                tracks.append(track_data)
                
        # Sort tracks by filename (usually contains track number)
        tracks.sort(key=lambda x: x['id'])
        return tracks
        
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse date string from Archive.org metadata
        """
        if not date_str:
            return None
            
        # Handle various date formats
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y.%m.%d',
            '%Y%m%d'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        return None
        
    def _clean_track_name(self, filename: str) -> str:
        """
        Clean track name from filename
        """
        # Remove file extension
        name = filename.rsplit('.', 1)[0]
        
        # Remove track numbers if present
        if name[0].isdigit():
            name = name.split(' ', 1)[1]
            
        return name
        
    async def get_show_details(self, identifier: str) -> Dict:
        """
        Get detailed information about a specific show
        """
        try:
            item = ia.get_item(identifier)
            
            return {
                'id': item.identifier,
                'date': self._parse_date(item.metadata.get('date')),
                'venue': item.metadata.get('venue'),
                'location': item.metadata.get('coverage'),
                'description': item.metadata.get('description'),
                'source': item.metadata.get('source'),
                'tracks': self._parse_tracks(item),
                'metadata': item.metadata
            }
            
        except Exception as e:
            logging.error(f"Error getting show details: {e}")
            raise
            
    async def download_track(self, identifier: str, filename: str, target_path: str):
        """
        Download a specific track from a show
        """
        try:
            item = ia.get_item(identifier)
            file = item.get_file(filename)
            file.download(target_path)
            
        except Exception as e:
            logging.error(f"Error downloading track: {e}")
            raise
