# app/api/shows.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..db.models import Show, Song
from ..core.auth import get_current_user
from ..services.cache_manager import CacheManager, QueueManager
import internetarchive as ia

router = APIRouter()
cache_manager = CacheManager()
queue_manager = QueueManager()

@router.get("/years")
async def get_available_years():
    
    print("Get all available years of shows")
    #TODO: add collection name as env variable
    query = "collection:TheJauntee"
    params = {'fields':'year'}
    search = ia.search_items(query, params=params)
    years = set()
    
    for result in search:
        year = result['year']
        if year in years:
            next
        else:
            years.add(year)

    print(f"Returning years of shows: {sorted(list(years), reverse=True)}")
    return sorted(list(years), reverse=True)

@router.get("/search")
async def search_shows(
    year: Optional[int] = None,
    venue: Optional[str] = None,
    date: Optional[str] = None
):
    """Search for shows with various filters"""
    query = "collection:TheJauntee"
    
    if year:
        query += f" AND year:{year}"
    if venue:
        query += f" AND venue:{venue}"
    if date:
        query += f" AND date:{date}"
        
    search_results = ia.search_items(query)
    shows = []
    count = 0
    
    for result in search_results:
        count += 1
        print(f"Searching for show #{count}")
        item = ia.get_item(result['identifier'])
        show_data = {
            'id': item.identifier,
            'date': item.metadata.get('date'),
            'venue': item.metadata.get('venue'),
            'location': item.metadata.get('coverage'),
            'description': item.metadata.get('description')
        }
        shows.append(show_data)
        
    return shows

@router.get("/{show_id}")
async def get_show_details(show_id: str):
    """Get detailed information about a specific show"""
    try:
        item = ia.get_item(show_id)
        
        # Get tracks information
        tracks = []
        for file in item.get_files():
            if file.format == 'VBR MP3':
                track = {
                    'id': file.name,
                    'name': file.name.split('.')[0],  # Remove extension
                    'size': file.size,
                    'length': file.length,
                    'format': file.format,
                    'bitrate': file.bitrate
                }
                tracks.append(track)
        
        show_data = {
            'id': item.identifier,
            'date': item.metadata.get('date'),
            'venue': item.metadata.get('venue'),
            'location': item.metadata.get('coverage'),
            'description': item.metadata.get('description'),
            'source': item.metadata.get('source'),
            'tracks': sorted(tracks, key=lambda x: x['name'])
        }
        
        return show_data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Show not found: {str(e)}")

@router.get("/{show_id}/stream/{filename}")
async def stream_track(
    show_id: str,
    filename: str,
    current_user: dict = Depends(get_current_user)
):
    """Get streaming information for a track"""
    # Check cache first
    cached_path = cache_manager.get_cached_path(show_id, filename)
    
    if cached_path:
        return {"cached_path": cached_path}
        
    # If not cached, queue for download and return direct IA stream URL
    await cache_manager.queue_download(show_id, filename)
    return {
        "stream_url": f"https://archive.org/download/{show_id}/{filename}",
        "is_caching": True
    }

@router.post("/{show_id}/queue/{filename}")
async def add_to_queue(
    show_id: str,
    filename: str,
    position: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Add a track to the user's queue"""
    queue_manager.add_to_queue(current_user["sub"], show_id, filename, position)
    return {"message": "Track added to queue"}

@router.get("/queue")
async def get_user_queue(current_user: dict = Depends(get_current_user)):
    """Get the user's current queue"""
    return queue_manager.get_queue(current_user["sub"])