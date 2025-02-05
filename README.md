# WhatsApp Chat Logger

This project is a Node.js script that listens for messages in specific WhatsApp groups, extracts relevant information (group name, sender name, timestamp, message, and phone number), and logs the messages into a CSV file. The log file is reset every hour to ensure fresh data collection.

## Features
- **Real-time logging** of WhatsApp group messages
- **Extracts sender's name, phone number, and timestamp**
- **Stores messages in a CSV file (`chat_logs.csv`)**
- **Automatically clears the log file every hour**
- **Displays structured message output in the console**

## Requirements
- Node.js installed
- WhatsApp Web account logged in
- `whatsapp-web.js` library

## Installation

1. Clone the repository or create a new project folder:
   ```sh
   git clone <repository_url>
   cd whatsapp-chat-logger
   ```

2. Install dependencies:
   ```sh
   npm install whatsapp-web.js qrcode-terminal fs path
   ```

3. Run the script:
   ```sh
   node index.js
   ```

## How It Works
- When the script runs, it generates a **QR code** for authentication.
- The user scans the QR code using WhatsApp Web to log in.
- Once authenticated, the script listens for messages from specified WhatsApp groups.
- The extracted data is formatted and stored in `chat_logs.csv`.
- Every hour, the log file is cleared and reset.

## Output Format
### Console Output
```
Group Name               Sender Name           Time Stamp           Message                        Phone Number
--------------------------------------------------------------------------------------------------------------
Developers Chat         John Doe              02/05/2025, 14:30     Hello team!                   2349012345678
Coding Group           Alice                 02/05/2025, 14:35     Any updates?                  2348098765432
```
### CSV File Output (`chat_logs.csv`)
```
Group Name,Sender Name,Time Stamp,Message,Phone Number
Developers Chat,John Doe,Hello team!,2349012345678,02/05/2025,14:30
Coding Group,Alice,Any updates?,2348098765432,02/05/2025,14:35
```

## To Get All Messages From Your WhatsApp
- **Uncomment the line //Get all WhatsApp messages.** This will allow you recieve all messges from your WhatsApp, statuses included.

## Customization
- **Modify Group IDs:** If you need to filter specific groups, update the `groupId1` and `groupId2` variables.
- **Adjust Log Retention:** Change the interval in `setInterval(clearLogFile, 60 * 60 * 1000);` to modify how often logs are cleared.

## Troubleshooting
- If the QR code doesn’t generate, ensure **WhatsApp Web** is not logged in elsewhere.
- If the script fails, delete the `session` folder and restart the script.

## Disclaimer
[!IMPORTANT] It is not guaranteed you will not be blocked by using this method. WhatsApp does not allow bots or unofficial clients on their platform, so this shouldn't be considered totally safe.

## License
This project is open-source and available under the Apache License.