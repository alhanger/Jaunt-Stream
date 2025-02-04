# app/services/cache_manager.py
import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..core.config import get_settings
from ..db.models import Show, Song
import internetarchive as ia

class CacheManager:
    def __init__(self):
        self.settings = get_settings()
        self.cache_dir = Path(self.settings.CACHE_DIR)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_cache_size = self.settings.MAX_CACHE_SIZE_GB * 1024 * 1024 * 1024  # Convert to bytes
        self._download_queue = asyncio.Queue()
        self._currently_downloading = set()
        
    async def start_cache_worker(self):
        """Start the background cache worker"""
        while True:
            try:
                show_id, filename = await self._download_queue.get()
                if (show_id, filename) not in self._currently_downloading:
                    self._currently_downloading.add((show_id, filename))
                    await self._download_file(show_id, filename)
                    self._currently_downloading.remove((show_id, filename))
                self._download_queue.task_done()
            except Exception as e:
                logging.error(f"Error in cache worker: {e}")

    async def queue_download(self, show_id: str, filename: str):
        """Add a song to the download queue"""
        await self._download_queue.put((show_id, filename))

    async def _download_file(self, show_id: str, filename: str):
        """Download a file using Internet Archive library and store it in cache"""
        cache_path = self.cache_dir / show_id / filename
        cache_path.parent.mkdir(exist_ok=True)
        
        if cache_path.exists():
            return str(cache_path)

        await self._ensure_cache_space()
        
        try:
            item = ia.get_item(show_id)
            file = item.get_file(filename)
            file.download(str(cache_path))
            return str(cache_path)
        except Exception as e:
            logging.error(f"Error downloading file: {e}")
            raise

    async def _ensure_cache_space(self):
        """Ensure there's enough space in the cache directory"""
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob('**/*') if f.is_file())
        
        if total_size > self.max_cache_size:
            # Get list of files sorted by access time
            files = [(f, f.stat().st_atime) for f in self.cache_dir.glob('**/*') if f.is_file()]
            files.sort(key=lambda x: x[1])
            
            # Remove oldest files until we're under the limit
            for file, _ in files:
                if total_size <= self.max_cache_size * 0.9:  # Leave 10% buffer
                    break
                size = file.stat().st_size
                file.unlink()
                total_size -= size

    def get_cached_path(self, show_id: str, filename: str) -> str:
        """Get the path to a cached file if it exists"""
        cache_path = self.cache_dir / show_id / filename
        return str(cache_path) if cache_path.exists() else None

class QueueManager:
    def __init__(self):
        self._queues = {}  # User-specific queues
        
    def create_queue(self, user_id: str):
        """Create a new queue for a user"""
        if user_id not in self._queues:
            self._queues[user_id] = {
                'current_index': -1,
                'songs': []
            }
            
    def add_to_queue(self, user_id: str, show_id: str, filename: str, position: int = None):
        """Add a song to a user's queue"""
        if user_id not in self._queues:
            self.create_queue(user_id)
            
        song_info = {
            'show_id': show_id,
            'filename': filename
        }
            
        if position is None:
            self._queues[user_id]['songs'].append(song_info)
        else:
            self._queues[user_id]['songs'].insert(position, song_info)
            
    def remove_from_queue(self, user_id: str, position: int):
        """Remove a song from a user's queue"""
        if user_id in self._queues:
            if 0 <= position < len(self._queues[user_id]['songs']):
                self._queues[user_id]['songs'].pop(position)
                
    def get_next_song(self, user_id: str) -> dict:
        """Get the next song in the queue"""
        if user_id in self._queues:
            queue = self._queues[user_id]
            if queue['current_index'] < len(queue['songs']) - 1:
                queue['current_index'] += 1
                return queue['songs'][queue['current_index']]
        return None
        
    def get_previous_song(self, user_id: str) -> dict:
        """Get the previous song in the queue"""
        if user_id in self._queues:
            queue = self._queues[user_id]
            if queue['current_index'] > 0:
                queue['current_index'] -= 1
                return queue['songs'][queue['current_index']]
        return None
        
    def clear_queue(self, user_id: str):
        """Clear a user's queue"""
        if user_id in self._queues:
            self._queues[user_id] = {
                'current_index': -1,
                'songs': []
            }
            
    def get_queue(self, user_id: str) -> list:
        """Get the current queue for a user"""
        if user_id in self._queues:
            return self._queues[user_id]['songs']
        return []