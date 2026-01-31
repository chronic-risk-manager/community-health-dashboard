import os
import sys

# Add the src directory to the Python path to allow relative imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

import models
import database

def create_database_tables():
    print("Attempting to create database tables...")
    try:
        # Ensure the data directory exists
        os.makedirs(database.DATA_DIR, exist_ok=True)
        
        # Delete existing database file if it exists to ensure a clean slate
        db_path = os.path.join(database.DATA_DIR, 'community_health.db')
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed existing database file: {db_path}")
        
        models.Base.metadata.create_all(bind=database.engine)
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_database_tables()
