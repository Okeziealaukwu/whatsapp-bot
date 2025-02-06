const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');


// Initialize the WhatsApp client
const client = new Client({
    authStrategy: new LocalAuth(), // Saves session to avoid scanning QR code every time
    puppeteer: { headless: true }   // Runs without opening a browser window
});

const logFile = path.join(__dirname, "chat_logs.csv"); // CSV file location
// const logFile = "chat_logs.txt"; // File to save chat messages in text file


// Generate and display the QR code for authentication
client.on('qr', qr => {
    console.log('Scan this QR code in WhatsApp:');
    qrcode.generate(qr, { small: true });
});


// Function to clear file every hour
function clearLogFile() {
    fs.writeFileSync(logFile, "Group Name,Sender Name,Message,Phone Number,Time Stamp\n"); // Reset file with headers
    console.log("Old messages cleared. Starting fresh...");
}

// Function to write a message to the file
function logMessageToFile(data) {
    fs.appendFileSync(logFile, data + "\n");
}

// When the client is ready
client.on('ready', () => {
    console.log('Client is ready!');

    const headers = `${"Group Name".padEnd(25)} ${"Sender Name".padEnd(20)} ${"Message".padEnd(30)} ${"Phone Number"} ${"Time Stamp".padEnd(22)}`;
    //Clear csv
    if (!fs.existsSync(logFile)) {
        logMessageToFile("Group Name,Sender Name,Message,Phone Number,Time Stamp");
    }

     // Print column headers
    console.log(headers);
    console.log('-'.repeat(120)); // Separator line for readability

        // Save headers to file use to get clean formatted txt file
        // logMessageToFile(headers);
        // logMessageToFile('-'.repeat(120));

    // Set interval to clear file every hour
    setInterval(clearLogFile, 60 * 60 * 1000);
});

// Function to format and log message
async function formatAndLogMessage(message) {
    const chat = await message.getChat();
    const sender = await message.getContact(); // Fetch sender's contact details
    const timestamp = new Date(message.timestamp * 1000).toLocaleString(); // Converts to local date & time
    const phoneNumber = sender.id._serialized.split('@')[0]; // Extract users number
    const senderName = sender.pushname || sender.name || "Unknown";
    const formattedMessage = `${chat.name.padEnd(25)} ${senderName.padEnd(20)} ${message.body.padEnd(30)} ${phoneNumber} ${timestamp.padEnd(22)}`;
    const csvformattedMessage = `${chat.name}, ${senderName}, ${message.body}, ${phoneNumber}, ${timestamp}`;

    console.log(formattedMessage); // Log in console
    logMessageToFile(csvformattedMessage); // Save to file
}

//Get all WhatsApp messages.
// client.on('message', async message => {
//     await formatAndLogMessage(message);
// });

//Get specific WhatsApp messages from groups
const groupId1 = 'xxxxxxxx';  // Replace with actual group ID
const groupId2 = 'xxxxxxxx';  // Replace with actual group ID

client.on('message', async message => {
    if (message.from === groupId1 || message.from === groupId2) {
        await formatAndLogMessage(message);
    }
});

// Start the client
client.initialize();
