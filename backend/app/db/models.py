# app/db/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# Association table for user favorites (shows)
show_favorites = Table(
    'show_favorites',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id')),
    Column('show_id', String)
)

# Association table for user favorites (songs)
song_favorites = Table(
    'song_favorites',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id')),
    Column('song_id', String)
)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)  # Auth0 user ID
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    favorite_shows = relationship("Show", secondary=show_favorites, backref="favorited_by")
    favorite_songs = relationship("Song", secondary=song_favorites, backref="favorited_by")
    playlists = relationship("Playlist", back_populates="user")

class Show(Base):
    __tablename__ = 'shows'
    
    id = Column(String, primary_key=True)  # Archive.org identifier
    date = Column(DateTime, index=True)
    venue = Column(String)
    location = Column(String)
    archive_url = Column(String)
    cached = Column(Boolean, default=False)
    cache_path = Column(String, nullable=True)

class Song(Base):
    __tablename__ = 'songs'
    
    id = Column(String, primary_key=True)
    name = Column(String)
    duration = Column(Integer)  # Duration in seconds
    show_id = Column(String, ForeignKey('shows.id'))
    track_number = Column(Integer)
    set_number = Column(Integer)
    cached = Column(Boolean, default=False)
    cache_path = Column(String, nullable=True)

    # Relationship
    show = relationship("Show", backref="songs")

class Playlist(Base):
    __tablename__ = 'playlists'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    user_id = Column(String, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="playlists")
    songs = relationship("PlaylistSong", back_populates="playlist")

class RecentlyPlayed(Base):
    __tablename__ = 'recently_played'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    song_id = Column(String, ForeignKey('songs.id'))
    played_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="recently_played")
    song = relationship("Song")

class PlaylistSong(Base):
    __tablename__ = 'playlist_songs'
    
    id = Column(Integer, primary_key=True)
    playlist_id = Column(Integer, ForeignKey('playlists.id'))
    song_id = Column(String, ForeignKey('songs.id'))
    position = Column(Integer)
    
    # Relationships
    playlist = relationship("Playlist", back_populates="songs")
    song = relationship("Song")