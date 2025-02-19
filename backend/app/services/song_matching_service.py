from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import pandas as pd
import json
from typing import List, Dict, Tuple
import csv
from data_sync_service import ArchiveScraper

class SongMatcher:
    def __init__(self, master_titles: List[str], threshold: int = 85):
        """
        Initialize the song matcher with a list of master song titles.
        
        Args:
            master_titles: List of correct song titles
            threshold: Minimum similarity score (0-100) to consider a match
        """
        self.master_titles = master_titles
        self.threshold = threshold
        self.match_cache = {}  # Cache for performance optimization
        
    def _preprocess_title(self, title: str) -> str:
        """
        Preprocess a song title for better matching.
        
        Args:
            title: Raw song title
            
        Returns:
            Preprocessed title
        """
        # Convert to lowercase
        title = title.lower()
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = ['the ', 'a ']
        for prefix in prefixes_to_remove:
            if title.startswith(prefix):
                title = title[len(prefix):]
                
        # Remove special characters and extra whitespace
        title = ''.join(c for c in title if c.isalnum() or c.isspace())
        title = ' '.join(title.split())
        
        return title
        
    def find_best_match(self, source_title: str) -> Tuple[str, int]:
        """
        Find the best matching master title for a given source title.
        
        Args:
            source_title: Title to find a match for
            
        Returns:
            Tuple of (best matching title, similarity score)
        """
        if source_title in self.match_cache:
            return self.match_cache[source_title]
            
        processed_source = self._preprocess_title(source_title)
        
        # Try exact match first
        for master_title in self.master_titles:
            if self._preprocess_title(master_title) == processed_source:
                self.match_cache[source_title] = (master_title, 100)
                return master_title, 100
        
        # Use fuzzy matching
        score_threshold=75
        matches = process.extractBests(
            processed_source,
            [self._preprocess_title(t) for t in self.master_titles],
            scorer=fuzz.ratio,
            score_cutoff=score_threshold,
            limit=3
        )
        
        best_match_index = None
        best_match = None
        score = 0
        
        if matches:
            # print(f"No matches meeting {score_threshold}%")
            best_match_name = matches[0][0]  # Get index of best match
            best_match = self.master_titles.index(best_match_name)
            score = matches[0][1]
        
        self.match_cache[source_title] = (best_match, score)
        return best_match, score
        
    def process_archive_data(self, archive_data: List[Dict]) -> List[Dict]:
        """
        Process a list of archive.org show data and standardize song titles.
        
        Args:
            archive_data: List of show dictionaries from archive.org
            
        Returns:
            Processed show data with standardized titles
        """
        processed_data = []
        
        for show in archive_data:
            processed_show = show.copy()
            if 'tracks' in show:
                processed_tracks = []
                for track in show['tracks']:
                    track_copy = track.copy()
                    best_match, score = self.find_best_match(track['name'])
                    
                    if score >= self.threshold:
                        track_copy['original_name'] = track['name']
                        track_copy['name'] = best_match
                        track_copy['match_score'] = score
                    else:
                        # Keep original if no good match found
                        track_copy['needs_review'] = True
                        track_copy['best_match'] = best_match
                        track_copy['match_score'] = score
                        
                    processed_tracks.append(track_copy)
                    
                processed_show['tracks'] = processed_tracks
            processed_data.append(processed_show)
            
        return processed_data
        
    def generate_matching_report(self, processed_data: List[Dict]) -> Dict:
        """
        Generate a report of the matching process.
        
        Args:
            processed_data: Processed show data
            
        Returns:
            Dictionary containing matching statistics and issues
        """
        total_tracks = 0
        matched_tracks = 0
        needs_review = []
        match_scores = []
        
        for show in processed_data:
            if 'tracks' in show:
                for track in show['tracks']:
                    total_tracks += 1
                    if 'needs_review' not in track:
                        matched_tracks += 1
                        match_scores.append(track['match_score'])
                    else:
                        needs_review.append({
                            'show_date': show.get('date', 'Unknown'),
                            'original_title': track['name'],
                            'suggested_match': track['best_match'],
                            'score': track['match_score']
                        })
        
        return {
            'total_tracks': total_tracks,
            'matched_tracks': matched_tracks,
            'match_rate': matched_tracks / total_tracks if total_tracks > 0 else 0,
            'average_match_score': sum(match_scores) / len(match_scores) if match_scores else 0,
            'needs_review': sorted(needs_review, key=lambda x: x['score'], reverse=True)
        }

def save_matching_results(processed_data: List[Dict], report: Dict, output_path: str):
    """
    Save the matching results and report to files.
    
    Args:
        processed_data: Processed show data
        report: Matching report
        output_path: Base path for output files
    """
    # Save processed data
    with open(f"{output_path}_processed_data.json", 'w') as f:
        json.dump(processed_data, f, indent=2)
        
    # Save report
    with open(f"{output_path}_matching_report.json", 'w') as f:
        json.dump(report, f, indent=2)
        
    # Save needs review as CSV for easy viewing
    if report['needs_review']:
        pd.DataFrame(report['needs_review']).to_csv(
            f"{output_path}_needs_review.csv",
            index=False
        )

def csv_to_list(file_path):
    data_list = []
    try:
        with open(file_path, 'r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:

                if row:
                    data_list.append(row[0])
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return []
    except Exception as e:
         print(f"An error occurred: {e}")
         return []
    return data_list


# Example usage:
if __name__ == "__main__":
    # Example master titles
    master_titles = csv_to_list('/Users/alhanger/Documents/Personal/The Jauntee Web App/jauntee-music-stream/backend/app/services/jauntee_tracks_cleaned.csv')
    data_dir = "/Users/alhanger/Documents/Personal/The Jauntee Web App/jauntee-music-stream/jaunt-data"
    
    # Initialize matcher
    matcher = SongMatcher(master_titles)
    scraper = ArchiveScraper(data_dir)
    
    # Process archive data
    # archive_data = ... # Load your archive.org data here

    archive_data = scraper.load_show_data()
    processed_data = matcher.process_archive_data(archive_data)
    report = matcher.generate_matching_report(processed_data)
    save_matching_results(processed_data, report, "output/song_matching")