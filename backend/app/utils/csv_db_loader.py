import pandas as pd
import os
import sqlite3
from typing import Optional

def load_csv_to_sqlite(
    csv_path: str,
    db_path: str,
    table_name: str,
    if_exists: str = 'replace',
    index: bool = False,
    dtype: Optional[dict] = None
) -> None:
    """
    Load a CSV file into a SQLite database table.
    
    Args:
        csv_path: Path to the CSV file
        db_path: Path to the SQLite database
        table_name: Name of the table to create/update
        if_exists: How to behave if table exists ('fail', 'replace', or 'append')
        index: Whether to write DataFrame index as a column
        dtype: Optional dictionary of column dtypes
    """
    try:
        # Ensure the CSV file exists
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
            
        # Read the CSV file
        print(f"Reading CSV file: {csv_path}")
        
        # First, let's examine the first few lines of the file
        with open(csv_path, 'r') as f:
            print("\nFirst 5 lines of the CSV file:")
            for i, line in enumerate(f):
                if i < 5:
                    print(f"Line {i+1}: {line.strip()}")
                else:
                    break
                    
        # Try to read with more robust parsing options
        try:
            # Read single column CSV with potential commas in values
            df = pd.read_csv(
                csv_path,
                quoting=pd.io.common.QUOTE_ALL,  # Quote all fields
                quotechar='"',                   # Use double quotes
                header=0,                        # First row is header
                names=['title'],                 # Force column name
                encoding='utf-8'
            )
        except Exception as e:
            print(f"\nFirst attempt failed: {str(e)}")
            print("\nTrying alternative parsing method...")
            
            # If that fails, try reading with different options
            df = pd.read_csv(
                csv_path,
                dtype=dtype,
                sep=None,  # Let pandas detect the separator
                engine='python',  # More flexible but slower engine
                on_bad_lines='skip',  # Skip problematic lines
                encoding='utf-8'
            )
        
        print(f"Found {len(df)} rows and {len(df.columns)} columns")
        print("\nColumn names:")
        for col in df.columns:
            print(f"- {col}")
            
        # Create database connection
        print(f"\nConnecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        
        # Write to SQLite
        print(f"Writing to table: {table_name}")
        df.to_sql(
            name=table_name,
            con=conn,
            if_exists=if_exists,
            index=index
        )
        
        # Verify the data
        cursor = conn.cursor()
        row_count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"\nSuccessfully wrote {row_count} rows to {table_name}")
        
        # Show sample of the data
        print("\nFirst few rows in the database:")
        sample_query = f"SELECT * FROM {table_name} LIMIT 5"
        print(pd.read_sql_query(sample_query, conn))
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Example usage:
    csv_path = "/Users/alhanger/Documents/Personal/The Jauntee Web App/jauntee-music-stream/backend/app/services/jauntee_tracks_cleaned.csv"
    db_path = "/Users/alhanger/Documents/Personal/The Jauntee Web App/jauntee-music-stream/jaunt-data/jauntee_archive.db"
    table_name = "master_tracks"
    
    # Optional: Specify column data types
    dtype_mapping = {
        'id': 'int',
        'title': 'str',
        'aliases': 'str',
        'notes': 'str'
        # Add other columns as needed
    }
    
    load_csv_to_sqlite(
        csv_path=csv_path,
        db_path=db_path,
        table_name=table_name,
        if_exists='replace',  # 'fail', 'replace', or 'append'
        dtype=dtype_mapping
    )