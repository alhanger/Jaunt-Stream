import re
import csv
import pandas as pd
from typing import List, Set

class SongTitleSanitizer:
    # Define constants for frequently used patterns
    SYMBOLS_PATTERN = r'[_^*+$@#%&]'
    ARROWS_PATTERN = r'\s*(?:->|>)\s*'
    TRAILING_HYPHEN_PATTERN = r'-\s*$'
    TRACK_NUMBER_PATTERN = r'^\d+[\s\.-]+'
    SHOW_IDENTIFIER_PATTERN = r'^jauntee\d{4}-\d{2}-\d{2}s\d+t\d+'
    WHITESPACE_PATTERN = r'\s+'

    def __init__(self):
        # Compile regex patterns for better performance
        self.symbols_regex = re.compile(self.SYMBOLS_PATTERN)
        self.arrows_regex = re.compile(self.ARROWS_PATTERN)
        self.trailing_hyphen_regex = re.compile(self.TRAILING_HYPHEN_PATTERN)
        self.track_number_regex = re.compile(self.TRACK_NUMBER_PATTERN)
        self.show_identifier_regex = re.compile(self.SHOW_IDENTIFIER_PATTERN)
        self.whitespace_regex = re.compile(self.WHITESPACE_PATTERN)

    def sanitize_songs(self, songs: List[str]) -> List[str]:
        """
        Main method to process a list of song titles and return sanitized unique titles.
        
        Args:
            songs: List of song titles to process
            
        Returns:
            List of sanitized unique song titles
        """
        sanitized_songs: Set[str] = set()  # Use set for automatic deduplication
        
        for song in songs:
            if not song:  # Skip empty strings
                continue
                
            # First remove symbols and clean basic formatting
            cleaned_song = self._clean_basic_formatting(song)
            
            # Process songs with transitions (contains arrows)
            if self.arrows_regex.search(cleaned_song):
                split_songs = self._split_multiple_songs(cleaned_song)
                sanitized_songs.update(split_songs)
            else:
                sanitized_song = self._sanitize_single_track(cleaned_song)
                if sanitized_song:  # Only add non-empty strings
                    sanitized_songs.add(sanitized_song)
        
        return sorted(list(sanitized_songs))  # Convert back to sorted list
    
    def _clean_basic_formatting(self, title: str) -> str:
        """Remove symbols and clean up basic formatting."""
        # Remove special characters
        title = self.symbols_regex.sub('', title)
        # Clean up whitespace
        title = self.whitespace_regex.sub(' ', title)
        return title.strip()
    
    def _split_multiple_songs(self, title: str) -> Set[str]:
        """Split and sanitize titles containing multiple songs."""
        songs = self.arrows_regex.split(title)
        return {self._sanitize_single_track(song) for song in songs if song.strip()}
    
    def _sanitize_single_track(self, title: str) -> str:
        """Sanitize a single track title."""
        # Remove show identifier if present
        title = self.show_identifier_regex.sub('', title)
        # Remove track numbers
        title = self.track_number_regex.sub('', title)
        # Remove trailing hyphen
        title = self.trailing_hyphen_regex.sub('', title)
        # Clean up whitespace
        title = self.whitespace_regex.sub(' ', title)
        return title.strip()
    
    def write_clean_songs(self):
        # logging.info("Writing tracks to CSV")
        # Open CSV file with proper headers
        data_dir = "/Users/alhanger/Documents/Personal/The Jauntee Web App/jauntee-music-stream/backend/app/services/jauntee_tracks.csv"
        data = pd.read_csv(data_dir, usecols=[0])['title'].tolist()

        sanitizer = SongTitleSanitizer()
        songs = sanitizer.sanitize_songs(data)
        print("Sanitized songs before writing")
        
        with open('jauntee_tracks_cleaned.csv', 'w', newline='', encoding='utf-8') as csvfile:
            print("Starting to write songs")
            writer = csv.DictWriter(csvfile, fieldnames=['title'])
            writer.writeheader()

            for song in songs:
                print(f"Writing {song}")
                writer.writerow({
                    'title': song
                })
        
            
    

def main():
    sanitizer = SongTitleSanitizer()
    sanitizer.write_clean_songs()
    print("Done!")

if __name__ == "__main__":
    main()