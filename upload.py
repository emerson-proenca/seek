"""
Loads Supabase Secrets
Finds 'output.json'
Uploads 'output.json' to Supabase
"""

import json

from load_env import supabase


def upload_to_supabase(json_file_path: str):
    """Reads JSON data and uploads it to the Supabase 'subito' table."""

    # Read data from the JSON file
    try:
        with open(json_file_path, "r", encoding="utf-8") as file:
            ads_data = json.load(file)
    except FileNotFoundError:
        print(f"Error: The file {json_file_path} was not found.")
        return
    except json.JSONDecodeError:
        print("Error: Invalid JSON format.")
        return

    # Prepare data for insertion
    formatted_data = []
    for item in ads_data:
        formatted_data.append(
            {
                "title": item.get("title"),
                "price": item.get("price"),
                "url": item.get("url"),
                "image": item.get("image"),
            }
        )

    # Upload data to Supabase
    try:
        # Upsert ignores duplicates based on the unique 'url' constraint
        response = (
            supabase.table("subito").upsert(formatted_data, on_conflict="url").execute()
        )

        print(f"Success! Uploaded {len(response.data)} records to the 'subito' table.")

    except Exception as e:
        print(f"An error occurred during the upload process: {e}")


if __name__ == "__main__":
    upload_to_supabase("output.json")
