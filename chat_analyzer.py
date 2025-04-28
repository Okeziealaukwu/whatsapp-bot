# import pandas as pd
# import re
# import os
# from openpyxl import load_workbook

# # Read CSV file into a DataFrame.
# df = pd.read_csv('chat_logs.csv', on_bad_lines='skip')


# # # --- Define the specific regex patterns for each parameter ---
# # patterns = {
# #     "Empty": r"Empty:\s*(\d+)",
# #     "Standby": r"Standby:\s*(\d+)",
# #     "Decanting": r"Decanting:\s*(\d+)",
# #     "In transit": r"In transit:\s*(\d+)",
# #     "Inlet pressure": r"Inlet pressure:\s*([\d.]+)bar",
# #     "Inlet temp": r"Inlet temp:\s*([\d.]+)[°⁰]C",
# #     "Flow rate": r"Flow rate:\s*([\d.]+)scm/hr",
# #     "Total flow": r"Total flow:\s*([\d.]+)scm",
# #     "Discharge Temp": r"Discharge Temp:\s*([\d.]+)[°⁰]C",
# #     "Discharge Pressure": r"Discharge Pressure:\s*([\d.]+)bar",
# #     "Skid No": r"Skid No:\s*(\d+)"
# # }

# # # --- Initialize a list to store log data rows ---
# # log_entries = []

# # # --- Process each row of df ---

# # for idx, row in df.iterrows():
# #     message = str(row.iloc[1])  # 3rd column: message text
    
# #     # Count how many parameters are found in this message
# #     count = 0
# #     for regex in patterns.values():
# #         if re.search(regex, message):
# #             count += 1

# #     # Check if message qualifies as a log (at least 4 parameters)
# #     if count >= 4:
# #         # Extract date and time from the designated columns
# #         date_val = row.iloc[3]
# #         time_val = row.iloc[4]
        
# #         # Initialize a dictionary with date and time
# #         log_data = {"Date": date_val, "Time": time_val}
        
# #         # Apply each specific regex to extract the parameter value
# #         for param, regex in patterns.items():
# #             match = re.search(regex, message)
# #             if match:
# #                 value_str = match.group(1)
# #                 # Convert the extracted value to int or float as appropriate
# #                 value = float(value_str) if '.' in value_str else int(value_str)
# #                 log_data[param] = value
# #             else:
# #                 # If parameter is missing, store None
# #                 log_data[param] = None

# #         # Append the extracted data to the log_entries list
# #         log_entries.append(log_data)

# # # --- Create the new DataFrame with log data ---
# # df_log = pd.DataFrame(log_entries)

# df_log = df.copy()

# # --- Append the log data to an Excel file ---

# # Specify the Excel file and sheet name
# excel_file = "log_data.xlsx"
# sheet_name = "Logs"

# # Check if the file already exists
# if os.path.exists(excel_file):
#     # Load the existing workbook
#     book = load_workbook(excel_file)
#     startrow = book[sheet_name].max_row if sheet_name in book.sheetnames else 0
    
#     # Write to Excel using context manager
#     with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
#         df_log.to_excel(writer, sheet_name=sheet_name, index=False, 
#                        startrow=startrow, header=(startrow == 0))
# else:
#     # Create new file if it doesn't exist
#     with pd.ExcelWriter(excel_file, engine='openpyxl', mode='w') as writer:
#         df_log.to_excel(writer, sheet_name=sheet_name, index=False)


# print(f"Chat logs saved to {excel_file} successfully!")

print("Hello World!)