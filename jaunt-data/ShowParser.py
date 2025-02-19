import re
from sqlalchemy import text
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ShowMetadata:
    date: str = None
    venue: str = None
    location: str = None
    source: str = None
    recording_info: str = None
    additional_notes: List[str] = None


def parse_setlist_and_metadata(description: str) -> Tuple[List[str], ShowMetadata]:
    """
    Parse both setlist and metadata from show description.
    Returns tuple of (track_names, metadata)
    """
    # Remove HTML tags and split into lines
    description = re.sub(r'<[^>]+>', '', description)
    lines = [line.strip() for line in description.split('\n') if line.strip()]

    metadata = ShowMetadata(additional_notes=[])
    track_names = []
    in_setlist = False

    for line in lines:
        # Try to identify what type of line this is
        if re.match(r'^\d{4}-\d{2}-\d{2}$', line):
            metadata.date = line
            continue

        if line.lower().startswith('source:'):
            metadata.source = line
            continue

        if line.lower().startswith('recorded') or line.lower().startswith('transfer:'):
            metadata.recording_info = line
            continue

        # Look for setlist markers
        if re.match(r'^set\s*\d', line.lower()) or re.match(r'^s\dt\d{2}\s*-', line.lower()):
            in_setlist = True
            continue

        # Parse track names - handle multiple formats
        if in_setlist:
            # Format: "s1t01 - Track Name" or "01. Track Name"
            track_match = re.match(r'^(?:s\dt\d{2}\s*-\s*|\d{2}\.\s*)(.*)', line)
            if track_match:
                track_name = track_match.group(1).strip()
                # Remove transition markers
                track_name = re.sub(r'[>-]\s*$', '', track_name).strip()
                track_names.append(track_name)
                continue

        # If we haven't matched anything else and we're not in the setlist yet,
        # try to identify venue/location
        if not in_setlist and not metadata.venue:
            # Skip known non-venue lines
            if not any(skip in line.lower() for skip in ['source:', 'recorded', 'transfer:', 'the jauntee']):
                if not metadata.venue:
                    metadata.venue = line
                elif not metadata.location:
                    metadata.location = line
                continue

        # Capture additional notes
        if in_setlist and not re.match(r'^(?:s\dt\d{2}\s*-\s*|\d{2}\.\s*)', line):
            metadata.additional_notes.append(line)

    return track_names, metadata


def create_track_mapping(track_names: List[str], filenames: List[str]) -> Dict[str, str]:
    """Create mapping between track filenames and actual track names."""
    mapping = {}

    # Group filenames by set
    set_groups = {}
    for filename in filenames:
        # Match both d1t01 and s1t01 format
        match = re.match(r'.*(?:d|s)(\d)t(\d{2})', filename)
        if match:
            set_num = match.group(1)
            if set_num not in set_groups:
                set_groups[set_num] = []
            set_groups[set_num].append(filename)

    # Sort filenames within each set
    for set_num in set_groups:
        set_groups[set_num].sort()

    # Create flat list of sorted filenames
    sorted_filenames = []
    for set_num in sorted(set_groups.keys()):
        sorted_filenames.extend(set_groups[set_num])

    # Map filenames to track names
    for filename, track_name in zip(sorted_filenames, track_names):
        if track_name:  # Only map if we have a track name
            mapping[filename] = track_name

    return mapping


def update_track_names(db, show_id: str, mapping: Dict[str, str], metadata: ShowMetadata = None):
    """Update track names and show metadata in database."""
    try:
        # Update track names
        update_tracks_stmt = text("""
            UPDATE songs 
            SET name = :track_name 
            WHERE id = :filename AND show_id = :show_id
        """)

        for filename, track_name in mapping.items():
            db.execute(
                update_tracks_stmt,
                {
                    'track_name': track_name,
                    'filename': filename,
                    'show_id': show_id
                }
            )

        # Update show metadata if provided
        if metadata:
            update_fields = {}
            if metadata.date:
                try:
                    parsed_date = datetime.strptime(metadata.date, '%Y-%m-%d')
                    update_fields['date'] = parsed_date
                except ValueError:
                    pass
            if metadata.venue:
                update_fields['venue'] = metadata.venue
            if metadata.location:
                update_fields['location'] = metadata.location
            if metadata.source:
                update_fields['source'] = metadata.source

            if update_fields:
                # Construct the UPDATE statement dynamically
                set_clauses = [f"{k} = :{k}" for k in update_fields.keys()]
                update_shows_stmt = text(f"""
                    UPDATE shows 
                    SET {', '.join(set_clauses)}
                    WHERE id = :show_id
                """)

                # Add show_id to parameters
                update_fields['show_id'] = show_id

                # Execute the update
                db.execute(update_shows_stmt, update_fields)

        db.commit()

    except Exception as e:
        db.rollback()
        raise Exception(f"Error updating database: {str(e)}")


def insert_songs(db, show_id: str, description: str):
    """Insert songs from description into empty songs table."""
    track_names, metadata = parse_setlist_and_metadata(description)

    # Extract set and track numbers from description
    for track_num, name in enumerate(track_names, 1):
        # Determine set number (assume set 1 if can't be determined)
        set_num = 1
        if track_num > len(track_names) // 2:
            set_num = 2

        # Create track ID in the format: jaunteeYYYY-MM-DDdStNN
        track_id = f"{show_id}d{set_num}t{track_num:02d}"

        stmt = text("""
            INSERT INTO songs (id, name, show_id, track_number, set_number)
            VALUES (:id, :name, :show_id, :track_number, :set_number)
        """)

        db.execute(stmt, {
            'id': track_id,
            'name': name,
            'show_id': show_id,
            'track_number': track_num,
            'set_number': set_num
        })

    db.commit()
    return len(track_names)


def process_show(db, show_id: str):
    """Process a show, handling empty songs table."""
    try:
        # Check if songs exist for this show
        check_stmt = text("SELECT COUNT(*) FROM songs WHERE show_id = :show_id")
        count = db.execute(check_stmt, {'show_id': show_id}).scalar()

        # Get show description
        show_stmt = text("SELECT description FROM show_transform_test WHERE id = :show_id")
        show_result = db.execute(show_stmt, {'show_id': show_id}).first()

        if not show_result or not show_result.description:
            return 0

        if count == 0:
            # No songs exist - insert them
            return insert_songs(db, show_id, show_result.description)
        else:
            # Update existing songs
            tracks_stmt = text("SELECT id FROM songs WHERE show_id = :show_id ORDER BY id")
            track_ids = [row[0] for row in db.execute(tracks_stmt, {'show_id': show_id}).fetchall()]

            track_names, metadata = parse_setlist_and_metadata(show_result.description)
            mapping = create_track_mapping(track_names, track_ids)
            update_track_names(db, show_id, mapping, metadata)
            return len(mapping)

    except Exception as e:
        db.rollback()
        raise Exception(f"Error processing show: {str(e)}")


# Example usage:
if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    DATABASE_URL = "sqlite:///jauntee_archive.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    try:
        show_id = "jauntee2018-02-20.flac16"
        num_processed = process_show(db, show_id)
        print(f"Processed {num_processed} tracks")
    finally:
        db.close()


# Example usage with your test data
test_description = '''
<div>The Jauntee</div><div>2017-06-28</div><div>Southbound Smokehouse</div><div>Augusta, GA</div><div><br /></div><div>Source:  AKG C451E w/ CK1 > Sound Devices MixPre-D > Tascam DR-680 MKII @ 2496 > SDXC</div><div>Transfer: SDXC > Samplitude Pro X3 [Build 35] > TLH v2.7.0 (flac8, ffp) > Foobar2000 v1.3.10 (Live Show Tagger)</div><div>Location: ROC 10' from stage 8' in the air ORTF</div><div>Recorded and processed by Jeff Mitchell (jeffhmitchell@gmail.com)</div><div>uploaded to archive 2017-07-01</div><div><br /></div><div>Set 1</div><div>s1t01 - Intro</div><div>s1t02 - Know It All</div>
'''

track_names, metadata = parse_setlist_and_metadata(test_description)
print("Track Names:", track_names)
print("\nMetadata:")
print(f"Date: {metadata.date}")
print(f"Venue: {metadata.venue}")
print(f"Location: {metadata.location}")
print(f"Source: {metadata.source}")