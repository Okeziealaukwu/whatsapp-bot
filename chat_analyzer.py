import pandas as pd
import os
import re
import json
import sqlite3  # Using SQLite for demo purposes - deployment could be PostgreSQL, MySQL, etc as advised by IT.
from datetime import datetime
import traceback
# import sys

# -----------------------------
# File paths
# -----------------------------
csv_file = r"C:\Users\okezi\OneDrive\Documents\Git\whatsapp-bot-main\chat_logs.csv"
database_file = r"C:\Users\okezi\OneDrive\Documents\Git\whatsapp-bot-main\whatsapp_logs.db"
context_file = r"C:\Users\okezi\OneDrive\Documents\Git\whatsapp-bot-main\skid_context.json"

# -----------------------------
# Regex parameter mappings for different groups. Note each group needs a different regex as the message format is group specific
# -----------------------------
tempo_param_mapping = {
    "Skid in use": r"Skid in use:? ?(\d+)",
    "Decanting": r"Decanting:? ?(\d+)",
    "Standby skid": r"Standby skid:? ?(\d+)",
    "Empty skid": r"Empty skid:? ?(\d+|NIL)",
    "Inlet pressure": r"Inlet pressure:? ?([\d.]+) ?(?:Bar|B)?",
    "Flow rate": r"Flow rate:? ?([\d.]+) ?\(?SCM/HR\)?",
    "Interstage pressure": r"Interstage(?: pressure)?:? ?([\d.]+) ?(?:Bar|B)",
    "Total flow": r"Total flow:? ?([\d.]+)",
    "Discharge": r"Discharge:? ?([\d.]+) ?(?:bar|B)",
    "Outlet temp": r"Outlet temp:? ?([\d.]+)°C",
    "Inlet temp": r"Inlet temp:? ?([\d.]+)°C"
}

splendor_param_mapping = {
    "Skid in use": r"Skid in use: ?(\d+)",
    "Decanting": r"Decanting:? ?(\d+)",
    "Standby skid": r"Standby skid:? ?(\d+)",
    "Empty skid": r"Empty skid:? ?(\d+|NIL)",
    "Inlet pressure": r"Inlet pressure:? ?([\d.]+) ?(?:Bar|B)?",
    "Flow rate": r"Flow rate:? ?([\d.]+)",
    "Interstage pressure": r"Interstage(?: pressure)?:? ?([\d.]+) ?(?:Bar|B)",
    "Total flow": r"Total.*flow:? ?([\d.]+)",
    "Discharge": r"Discharge:? ?([\d.]+) ?(?:bar|B)",
    "Outlet temp": r"Outlet temp:? ?([\d.]+)°C",
    "Inlet temp": r"Inlet temp:? ?([\d.]+)°C"
}

nigachem_param_mapping = {
    "Empty": r"Empty:(\d+)",
    "Standby": r"Standby:(\d+)",
    "Decanting": r"Decanting:(\S*)",
    "Pressures": r"Pressures:([\d.]+)",
    "FLOW rate": r"FLOW rate :([\d.]+)",
    "TOTAL FLOW tm": r"TOTAL FLOW tm:([\d.]+)",
    "TOTAL FLOW ptz": r"TOTAL FLOW ptz:([\d.]+)",
    "Temperature": r"Temperature:([\d.]+)",
    "Discharge": r"Discharge:([\d.]+)"
}

wasil_param_mapping = {
    "Empty": r"Empty:(\d+)",
    "Standby": r"Standby:(\d+)",
    "Decanting": r"Decanting:(\d+)",
    "In transit": r"In transit:(\d+)",
    "Inlet pressure": r"Inlet pressure:([\d.]+)",
    "Inlet temp": r"Inlet temp:([\d.]+)",
    "Flow rate": r"Flow rate:([\d.]+)",
    "Total flow": r"Total flow:([\d.]+)",
    "Discharge Temp": r"Discharge Temp:([\d.]+)",
    "Discharge Pressure": r"Discharge Pressure:([\d.]+)",
    "Skid No": r"Skid No: (\d+)"
}

heirs_param_mapping = {
    # "Time": r"Time: ([\d\s]+[ap]m)",
    "HHOG Supply Pressure": r"HHOG Supply Pressure: ([\d.]+)",
    "CHGC AGI Pressure": r"CHGC AGI Pressure: ([\d.]+)",
    "CHGC AGI Flow rate": r"CHGC AGI Flow rate: (\d+) scm\/hr",
    "CHGC AGI Temperature": r"CHGC AGI\s+?Temperature: ([\d.]+)"
}

# -----------------------------
# Define which parameter to use for each group. CNG disatch group not included for now
# -----------------------------
group_mappings = {
    'Axxela CNG Supply to Tempo': {
        'params': tempo_param_mapping,
        'pressure_field': 'Inlet pressure',
        'flow_field': 'Total flow'
    },
    'CNG Supply to Splendor Electric': {
        'params': splendor_param_mapping,
        'pressure_field': 'Inlet pressure',
        'flow_field': 'Total flow'
    },
    'Nigachem CNG Supply': {
        'params': nigachem_param_mapping,
        'pressure_field': 'Pressures',
        'flow_field': 'TOTAL FLOW ptz'  
    },
    'Axxela CNG Wasil': {
        'params': wasil_param_mapping,
        'pressure_field': 'Inlet pressure',
        'flow_field': 'Total flow'
    }
}

# -----------------------------
# Load or initialize skid context
# -----------------------------
def load_skid_context():
    if os.path.exists(context_file):
        try:
            with open(context_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading context file: {e}")
            return {}
    else:
        return {}

def save_skid_context(context):
    with open(context_file, 'w') as f:
        json.dump(context, f, indent=4)

# -----------------------------
# Database setup functions
# -----------------------------
def initialize_database():
    """Create the database and tables if they don't exist"""
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    
    # Create a groups table to keep track of all the groups
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    ''')
    
    # Insert all our known groups
    for group_name in group_mappings.keys():
        cursor.execute("INSERT OR IGNORE INTO groups (name) VALUES (?)", (group_name,))
    
    # Commit and close
    conn.commit()
    conn.close()

def create_group_table(conn, group_name):
    """Create a table for a specific group if it doesn't exist"""
    # Sanitize the group name for table name
    table_name = sanitize_table_name(group_name)
    
    # Get all possible parameter names for this group
    param_columns = []
    if group_name in group_mappings:
        param_columns = list(group_mappings[group_name]['params'].keys())
    
    # Start with common columns
    columns = [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "date TEXT",
        "time TEXT",
        "is_new_skid TEXT",
        "skid_baseline_flow REAL",
        "decanted_volume REAL"
    ]
    
    # Add columns for each parameter
    for param in param_columns:
        # Sanitize parameter name for column name
        col_name = sanitize_column_name(param)
        
        # Determine column type based on parameter
        if param in ['Skid in use', 'Standby skid', 'Empty skid', 'Decanting', 
                    'Standby', 'Empty', 'Skid No', 'In transit']:
            col_type = "TEXT"
        else:
            col_type = "REAL"
        
        columns.append(f"{col_name} {col_type}")
    
    # Create the table
    create_table_sql = f'''
    CREATE TABLE IF NOT EXISTS "{table_name}" (
        {', '.join(columns)},
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    '''
    
    try:
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        conn.commit()
        print(f"Created or verified table for group: {group_name}")
        return True
    except Exception as e:
        print(f"Error creating table for {group_name}: {e}")
        conn.rollback()
        return False

def sanitize_table_name(name):
    """Convert a group name to a valid SQLite table name"""
    # Replace spaces and invalid characters with underscores
    sanitized = re.sub(r'[^\w]', '_', name)
    # Ensure it doesn't start with a number
    if sanitized[0].isdigit():
        sanitized = f"t_{sanitized}"
    return sanitized

def sanitize_column_name(name):
    """Convert a parameter name to a valid SQLite column name"""
    # Replace spaces and invalid characters with underscores
    sanitized = re.sub(r'[^\w]', '_', name)
    # Lowercase for consistency
    sanitized = sanitized.lower()
    # Ensure it doesn't start with a number
    if sanitized[0].isdigit():
        sanitized = f"c_{sanitized}"
    return sanitized

# -----------------------------
# Extraction function using the provided mapping.
# -----------------------------
def extract_parameters(message_text, param_mapping):
    results = {}
    for key, pattern in param_mapping.items():
        # Add re.IGNORECASE flag to make the pattern case insensitive
        m = re.search(pattern, message_text, re.IGNORECASE)
        results[key] = m.group(1) if m else None
    return results

# -----------------------------
# Processing function which incorporates skid tracking
# -----------------------------
def process_group(df_group, group_name, skid_context):
    # Get the appropriate configuration for this group
    if group_name not in group_mappings:
        print(f"No parameter mapping defined for group '{group_name}'. Skipping.")
        return None
    
    config = group_mappings[group_name]
    param_mapping = config['params']
    pressure_field = config['pressure_field']
    flow_field = config['flow_field']
    
    # Initialize context for this group if it doesn't exist or ensure all keys are present
    if group_name not in skid_context:
        skid_context[group_name] = {}
        
    # Ensure all required keys are present
    required_keys = ["last_pressure", "last_total_flow", "skid_baseline_flow", "last_skid_change"]
    for key in required_keys:
        if key not in skid_context[group_name]:
            skid_context[group_name][key] = None
    
    group_context = skid_context[group_name]
    processed_rows = []
    
    pressure_threshold = 5  # This figure is chosen arbitrarily and can be adjusted as needed. Pressure increase == New Skid
    
    for idx, row in df_group.iterrows():
        message = row['Message']
        params = extract_parameters(message, param_mapping)
        
        # Extract and convert critical values
        current_total_flow = params.get(flow_field)
        current_pressure = params.get(pressure_field)
        
        try:
            if current_total_flow is not None:
                current_total_flow = float(current_total_flow)
            if current_pressure is not None:
                current_pressure = float(current_pressure)
        except ValueError:
            current_total_flow = None
            current_pressure = None
        
        # Check for new skid (significant pressure increase)
        is_new_skid = False
        if (current_pressure is not None and 
            group_context["last_pressure"] is not None and 
            current_pressure > group_context["last_pressure"] + pressure_threshold):
            
            # Pressure increase indicates new skid
            is_new_skid = True
            group_context["skid_baseline_flow"] = group_context["last_total_flow"]
            group_context["last_skid_change"] = f"{row.iloc[4]} {row.iloc[5]}"  # Date and time
            # print(f"New skid detected for {group_name} at pressure {current_pressure}")
        
        # Calculate decanted volume: Instanteneous Meter Reading - Meter reading at the start of the skid decanting
        decanted_volume = None
        if current_total_flow is not None and group_context["skid_baseline_flow"] is not None:
            decanted_volume = current_total_flow - group_context["skid_baseline_flow"]
        
        # Update context with current values if they exist
        if current_pressure is not None:
            group_context["last_pressure"] = current_pressure
        if current_total_flow is not None:
            group_context["last_total_flow"] = current_total_flow
        
        # Initialize baseline flow if this is the first record with valid flow
        if group_context["skid_baseline_flow"] is None and current_total_flow is not None:
            group_context["skid_baseline_flow"] = current_total_flow
        
        # Process all parameters
        for key, value in params.items():
            try:
                # Keep some fields as strings
                if key not in ['Skid in use', 'Standby skid', 'Empty skid', 'Decanting', 'Standby', 'Empty', 'Skid No', 'In transit']:
                    params[key] = float(value) if value is not None else None
            except ValueError:
                params[key] = None
        
        # Only add records (rows) with valid data
        match_count = sum(1 for v in params.values() if v is not None)
        if match_count >= 3:
            date_str = row.iloc[4]
            time_str = row.iloc[5]
            
            # Create new row with tracking info
            new_row = {
                "date": date_str, 
                "time": time_str,
                "is_new_skid": "Yes" if is_new_skid else "No",
                "skid_baseline_flow": group_context["skid_baseline_flow"],
                "decanted_volume": decanted_volume
            }
            new_row.update(params)
            processed_rows.append(new_row)
    
    # Return processed DataFrame
    return pd.DataFrame(processed_rows) if processed_rows else None

# -----------------------------
# Database insertion function
# -----------------------------
def insert_data_to_db(conn, group_name, df):
    """Insert processed data into the database"""
    if df is None or df.empty:
        print(f"No data to insert for group '{group_name}'")
        return 0
    
    table_name = sanitize_table_name(group_name)
    cursor = conn.cursor()
    rows_inserted = 0
    
    # Check for existing entries to avoid duplicates
    existing_entries = set()
    try:
        cursor.execute(f'SELECT date, time FROM "{table_name}"')
        existing_entries = set((row[0], row[1]) for row in cursor.fetchall())
    except sqlite3.OperationalError:
        # Table might not exist yet
        pass
    
    for _, row in df.iterrows():
        # Skip if this date/time combination already exists
        if (row['date'], row['time']) in existing_entries:
            continue
        
        # Prepare column names and placeholders
        columns = []
        placeholders = []
        values = []
        
        for col, val in row.items():
            if val is not None:  # Only include non-null values
                columns.append(sanitize_column_name(col))
                placeholders.append('?')
                values.append(val)
        
        # Skip if no valid columns
        if not columns:
            continue
        
        # Construct and execute INSERT query
        query = f'INSERT INTO "{table_name}" ({", ".join(columns)}) VALUES ({", ".join(placeholders)})'
        try:
            cursor.execute(query, values)
            rows_inserted += 1
        except Exception as e:
            print(f"Error inserting row: {e}")
            conn.rollback()
    
    conn.commit()
    return rows_inserted

# -----------------------------
# Main processing
# -----------------------------
def main():
    # Load context
    skid_context = load_skid_context()
    
    # Initialize database
    initialize_database()
    
    # Load and process CSV
    df = pd.read_csv(csv_file)
    print("CSV loaded successfully with {} rows.".format(len(df)))
    
    # Check if CSV is empty - if so, exit gracefully
    if len(df) == 0:
        print("No data to process in CSV file. Exiting.")
        return
    
    # Clean up message text (to remove newlines and other unwanted characters)
    df.iloc[:, 2] = df.iloc[:, 2].astype(str).replace(r"\r?\n", " ", regex=True)
    grouped = df.groupby('Group Name')
    group_dfs_raw = {group_name: group_df.copy() for group_name, group_df in grouped}
    print("Found groups:", list(group_dfs_raw.keys()))
    
    # Process each group
    conn = sqlite3.connect(database_file)
    total_inserted = 0
    
    for group_name, group_df in group_dfs_raw.items():
        print(f"Processing group: {group_name}")
        
        # Create table for this group if it doesn't exist
        if not create_group_table(conn, group_name):
            print(f"Skipping group '{group_name}' due to table creation failure")
            continue
        
        # Process the group data
        processed_df = process_group(group_df, group_name, skid_context)
        if processed_df is not None:
            # Insert data into database
            rows_inserted = insert_data_to_db(conn, group_name, processed_df)
            total_inserted += rows_inserted
            print(f"Inserted {rows_inserted} new rows for group '{group_name}'")
        else:
            print(f"No valid data extracted for group '{group_name}'")
    
    conn.close()
    
    # Save updated context for the next rerun
    save_skid_context(skid_context)
    
    print(f"Process completed. Total of {total_inserted} new rows inserted into database.")



    

# # -----------------------------
# # Export to Excel function (This was commented out as excel does not support simultaneous read and write leading to corrupted file)
# # -----------------------------
# def export_to_excel(output_file=None):
#     """Export database data to Excel for reporting"""
#     if output_file is None:
#         output_file = r"C:\Users\okezi\OneDrive\Documents\Git\whatsapp-bot-main\whatsapp_logs_export.xlsx"
    
#     conn = sqlite3.connect(database_file)
    
#     # Get all group tables
#     cursor = conn.cursor()
#     cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'groups' AND name != 'sqlite_sequence'")
#     tables = cursor.fetchall()
    
#     # Export each table to a sheet
#     with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
#         for table in tables:
#             table_name = table[0]
#             # Read data from the table
#             df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
#             # Use the original group name for the sheet
#             cursor.execute("SELECT name FROM groups WHERE ? LIKE sanitize_table_name(name)", (table_name,))
#             result = cursor.fetchone()
#             sheet_name = result[0] if result else table_name
#             # Write to Excel
#             df.to_excel(writer, sheet_name=sheet_name, index=False)
    
#     conn.close()
#     print(f"Data exported to Excel: {output_file}")

if __name__ == '__main__':
    try:
        main()
        # Uncomment if you need Excel export
        # export_to_excel()
    except Exception as e:
        print(f"Error in main process: {e}")
        print(traceback.format_exc())

print("Hello World!")
