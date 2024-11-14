import sqlite3
import json
import base64
from datetime import datetime
import argparse

def decode_base64_to_dict(b64_data):
    """
    Decodes a base64-encoded JSON string to a dictionary.
    
    Parameters:
        b64_data (str): Base64-encoded JSON string.
        
    Returns:
        dict: Decoded JSON dictionary if decoding is successful; otherwise, an empty dictionary.
    """
    try:
        # Decode base64 to a JSON string and then load it as a dictionary
        decoded_json = base64.b64decode(b64_data).decode('utf-8')
        return json.loads(decoded_json)
    except (base64.binascii.Error, UnicodeDecodeError, json.JSONDecodeError):
        print("Warning: Could not decode base64 or parse JSON")
        return {}

def decode_configuration(config_str, main_attribut=None):
    """
    Decodes the Configuration JSON string and processes its fields based on known Attribut values.
    
    The function checks the `Version` of each attribute and decodes `b64encoded` only if `Version` is 2. 
    Otherwise, it leaves `b64encoded` as a base64-encoded string.
    
    Parameters:
        config_str (str): JSON string from the Configuration column of the database.
        main_attribut (str, optional): The main attribute (e.g., "ListOfDevices") to filter and print. Default is None to process all.
    
    Returns:
        dict: Processed configuration dictionary with decoded fields where applicable.
    """
    try:
        # Decode JSON string to a dictionary
        config_data = json.loads(config_str) if config_str else {}
        
        # If a specific main attribute is provided, filter to process just that one
        attributes_to_process = [main_attribut] if main_attribut else [ "ListOfGroups", "ListOfDevices", "PluginConf", "CoordinatorBackup"]
        
        for attribut_key in attributes_to_process:
            if attribut_key in config_data:
                attribut_data = config_data[attribut_key]
                
                # Decode TimeStamp to a readable format
                timestamp = attribut_data.get("TimeStamp")
                if timestamp:
                    attribut_data["TimeStamp"] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                
                # Handle the "b64encoded" field based on Version
                version = attribut_data.get("Version")
                b64_data = attribut_data.get("b64encoded")
                
                # Only decode b64encoded if Version is 3
                if b64_data and version == 3:
                    attribut_data["b64encoded"] = decode_base64_to_dict(b64_data)
                else:
                    attribut_data["b64encoded"] = b64_data  # Leave as base64 string
                
                # Convert Version to string if present
                if version is not None:
                    attribut_data["Version"] = str(version)
                
        return config_data
    except json.JSONDecodeError:
        print("Warning: Could not decode Configuration JSON")
        return {}

def fetch_hardware_records(database_path, main_attribut=None):
    """
    Connects to the SQLite database, retrieves records from the Hardware table, 
    decodes the Configuration field, and prints each record in JSON format.
    
    Parameters:
        database_path (str): Path to the SQLite database file.
        main_attribut (str, optional): The main attribute (e.g., "ListOfDevices") to filter and print. Default is None to print all.
    
    Output:
        None: The function prints each record in a structured JSON format to the console.
    """
    # Connect to the SQLite database
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Query to extract ID, Name, and Configuration from the Hardware table
    query = "SELECT ID, Name, Configuration FROM Hardware"

    try:
        # Execute the query and fetch all results
        cursor.execute(query)
        records = cursor.fetchall()
        
        # Display each record in JSON format
        for record in records:
            record_id = record[0]
            name = record[1]
            config_str = record[2]
            
            # Decode the Configuration field, optionally filtering to a specific main attribute
            configuration = decode_configuration(config_str, main_attribut)
            
            # Create a dictionary for JSON output
            record_data = {
                "ID": record_id,
                "Name": name,
                "Configuration": configuration
            }
            
            # Print the record data as a JSON string
            print(json.dumps(record_data, indent=4))
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the database connection
        conn.close()


def main():
    """
    Main function to parse command-line arguments and call the appropriate function to fetch hardware records.
    """
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Fetch hardware records from an SQLite database.")
    parser.add_argument("database", help="Path to the SQLite database file")
    parser.add_argument("--main_attribut", choices=[ "ListOfGroups", "ListOfDevices", "PluginConf", "CoordinatorBackup"],
                        help="Specify which main attribute to print (default is to print all)")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Fetch and print hardware records based on the provided arguments
    fetch_hardware_records(args.database, args.main_attribut)

# Run the script
if __name__ == "__main__":
    main()
