# app/services/recently_played.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from ..db.models import RecentlyPlayed, Song, Show
from ..core.config import get_settings

class RecentlyPlayedService:
    def __init__(self, db: Session):
        self.db = db
        self.max_history = 50  # Maximum number of tracks to keep in history
        
    async def add_played_song(self, user_id: str, song_id: str):
        """Add a song to user's recently played history"""
        # Create new recently played entry
        recently_played = RecentlyPlayed(
            user_id=user_id,
            song_id=song_id
        )
        self.db.add(recently_played)
        
        # Get count of user's history
        history_count = self.db.query(RecentlyPlayed)\
            .filter(RecentlyPlayed.user_id == user_id)\
            .count()
            
        # If exceeded max history, remove oldest entries
        if history_count > self.max_history:
            oldest_entries = self.db.query(RecentlyPlayed)\
                .filter(RecentlyPlayed.user_id == user_id)\
                .order_by(RecentlyPlayed.played_at)\
                .limit(history_count - self.max_history)\
                .all()
            
            for entry in oldest_entries:
                self.db.delete(entry)
                
        self.db.commit()
        
    async def get_recently_played(
        self, 
        user_id: str, 
        limit: int = 20,
        days: Optional[int] = None
    ) -> List[dict]:
        """Get user's recently played songs with show information"""
        query = self.db.query(
            RecentlyPlayed,
            Song,
            Show
        ).join(
            Song, RecentlyPlayed.song_id == Song.id
        ).join(
            Show, Song.show_id == Show.id
        ).filter(
            RecentlyPlayed.user_id == user_id
        )
        
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(RecentlyPlayed.played_at >= cutoff_date)
            
        recently_played = query.order_by(
            desc(RecentlyPlayed.played_at)
        ).limit(limit).all()
        
        return [{
            'song': {
                'id': song.id,
                'name': song.name,
                'duration': song.duration,
                'track_number': song.track_number,
                'set_number': song.set_number
            },
            'show': {
                'id': show.id,
                'date': show.date,
                'venue': show.venue,
                'location': show.location
            },
            'played_at': recent.played_at
        } for recent, song, show in recently_played]
        
    async def get_listening_stats(self, user_id: str, days: int = 30) -> dict:
        """Get listening statistics for a user"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get total plays
        total_plays = self.db.query(RecentlyPlayed)\
            .filter(
                RecentlyPlayed.user_id == user_id,
                RecentlyPlayed.played_at >= cutoff_date
            ).count()
            
        # Get most played songs
        most_played_songs = self.db.query(
            Song,
            func.count(RecentlyPlayed.id).label('play_count')
        ).join(
            RecentlyPlayed, RecentlyPlayed.song_id == Song.id
        ).filter(
            RecentlyPlayed.user_id == user_id,
            RecentlyPlayed.played_at >= cutoff_date
        ).group_by(
            Song.id
        ).order_by(
            desc('play_count')
        ).limit(10).all()
        
        # Get most played shows
        most_played_shows = self.db.query(
            Show,
            func.count(RecentlyPlayed.id).label('play_count')
        ).join(
            Song, Song.show_id == Show.id
        ).join(
            RecentlyPlayed, RecentlyPlayed.song_id == Song.id
        ).filter(
            RecentlyPlayed.user_id == user_id,
            RecentlyPlayed.played_at >= cutoff_date
        ).group_by(
            Show.id
        ).order_by(
            desc('play_count')
        ).limit(10).all()
        
        return {
            'total_plays': total_plays,
            'most_played_songs': [{
                'song': {
                    'id': song.id,
                    'name': song.name
                },
                'play_count': play_count
            } for song, play_count in most_played_songs],
            'most_played_shows': [{
                'show': {
                    'id': show.id,
                    'date': show.date,
                    'venue': show.venue
                },
                'play_count': play_count
            } for show, play_count in most_played_shows]
        }
