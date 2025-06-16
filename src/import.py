import csv
import os
from datetime import datetime, time, timezone
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from urllib.parse import urlparse

COLLECTION_NAME = 'iron_at'
MONGO_URI = os.environ['MONGO_URI']
CSV_FILE = os.environ['INPUT']

def get_db_name_from_uri(mongo_uri):
    """
    Extracts the database name from a MongoDB connection URI.
    Returns None if no database name is specified in the URI path.
    """
    try:
        parsed_uri = urlparse(mongo_uri)
        # The database name is typically the path component without the leading '/'
        db_name = parsed_uri.path.lstrip('/')
        return db_name if db_name else None
    except Exception as e:
        print(f"Warning: Could not parse database name from URI: {e}")
        return None

def import_csv_to_mongodb(csv_file_path, mongo_uri, collection_name):
    """
    Reads data from a CSV file, formats it, and pushes it to a MongoDB collection.
    The database name can be extracted from the URI or provided explicitly.

    Args:
        csv_file_path (str): The path to the CSV file.
        mongo_uri (str): The MongoDB connection URI (e.g., "mongodb+srv://user:pass@host/dbname").
        collection_name (str): The name of the MongoDB collection.
    """
    ranks_data = []
    try:
        with open(csv_file_path, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    ranks_data.append({
                        "name": row["Name"],
                        "score": int(row["Score"].replace(",", "")),  # Convert score to int
                        "tasks": row["Tasks"],
                        "position": int(row["Position"])
                    })
                except ValueError as ve:
                    print(f"Skipping row due to data conversion error: {row} - {ve}")
                except KeyError as ke:
                    print(f"Skipping row due to missing column: {ke} in row {row}")
    except FileNotFoundError:
        print(f"Error: CSV file not found at '{csv_file_path}'")
        return
    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")
        return

    if not ranks_data:
        print("No valid data found in the CSV file to import.")
        return

    # Determine the database name
    db_name = get_db_name_from_uri(mongo_uri)
    if not db_name:
        print("Error: No database name provided in the MongoDB URI.")
        print("Please ensure your URI includes a database name (e.g., /dbname).")
        return

    # Get current date
    current_date = datetime.combine(datetime.now(timezone.utc), time(0,0), timezone.utc)

    # Create the final document structure
    mongo_document = {
        "date": current_date,
        "ranks": ranks_data
    }

    print("\nDocument to be inserted into MongoDB:")
    print(mongo_document)
    print("-" * 50)

    # MongoDB insertion
    client = None # Initialize client to None
    try:
        client = MongoClient(mongo_uri)
        # The ping command is cheap and does not require auth.
        client.admin.command('ping')
        print("Successfully connected to MongoDB!")
        print(f"Targeting database: '{db_name}'")

        db = client[db_name]
        collection = db[collection_name]

        query = {"date": current_date}

        result = collection.replace_one(query, mongo_document, upsert=True)

        if result.upserted_id:
            print(f"New document inserted with _id: {result.upserted_id}")
        elif result.matched_count > 0:
            print(f"Existing document matched and replaced (matched count: {result.matched_count})")
        else:
            print("No document was upserted. Error?.")

    except ConnectionFailure as e:
        print(f"MongoDB connection failed: {e}. Please ensure MongoDB is running and accessible.")
    except OperationFailure as e:
        print(f"MongoDB operation failed: {e}. Check database/collection permissions or name.")
    except Exception as e:
        print(f"An unexpected error occurred during MongoDB operation: {e}")
    finally:
        if client: # Check if client was successfully initialized
            client.close()
            print("MongoDB connection closed.")

if __name__ == "__main__":
    import_csv_to_mongodb(CSV_FILE, MONGO_URI, COLLECTION_NAME)