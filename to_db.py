import os
import sqlite3
import json

class DatabaseManager:
    def __init__(self, db_name='papers.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection and create tables if they don't exist."""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """Create necessary database tables if they don't exist."""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT,
            details TEXT,
            abstract TEXT
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS arxiv_metadata (
            article_id VARCHAR(255) PRIMARY KEY,
            entry_id VARCHAR(255), 
            updated DATETIME,
            published DATETIME,
            title TEXT,
            authors TEXT,
            summary TEXT,
            comment TEXT,
            journal_ref TEXT,
            doi TEXT,
            primary_category VARCHAR(255),
            categories TEXT,
            links TEXT,
            pdf_url TEXT
        )''')

    def process_json_files(self, folder_path):
        """Process all JSON files in the specified folder and insert data into the database."""
        for filename in os.listdir(folder_path):
            if filename.endswith('.json'):
                file_path = os.path.join(folder_path, filename)
                self._process_single_json(file_path)

    def _process_single_json(self, file_path):
        """Process a single JSON file and insert its data into the database."""
        try:
            with open(file_path, 'r') as file:
                json_data = json.load(file)
                for entry in json_data:
                    self.cursor.execute('''
                    INSERT INTO papers (title, link, details, abstract) 
                    VALUES (?, ?, ?, ?)
                    ''', (entry['title'], entry['link'], entry['details'], entry['abstract']))
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")

    def commit(self):
        """Commit the current transaction."""
        if self.conn:
            self.conn.commit()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

def main():
    # Create an instance of DatabaseManager
    db_manager = DatabaseManager('papers2.db')
    
    try:
        # Connect to the database
        db_manager.connect()
        
        # Process JSON files from the 'pr' folder
        db_manager.process_json_files('pr')
        
        # Commit the changes
        db_manager.commit()
    finally:
        # Ensure the connection is closed
        db_manager.close()

if __name__ == "__main__":
    main()
