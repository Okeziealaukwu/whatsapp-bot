// Description: This script uses the WhatsApp Web API to log messages from specific groups into a CSV file.
// It also runs a Python script to analyze the chat data before clearing the log file.

const { Client, LocalAuth } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

// Initialize the WhatsApp client
const client = new Client({
  authStrategy: new LocalAuth(), // Saves session to avoid scanning QR code every time
  puppeteer: { headless: false }, // Runs without opening a browser window
});

const logFile = path.join(__dirname, "chat_logs.csv"); // CSV file location

// Generate and display the QR code for authentication
client.on("qr", (qr) => {
  console.log("Scan this QR code in WhatsApp:");
  qrcode.generate(qr, { small: true });
});

// Function to clear file only if Python script runs successfully
function clearLogFile() {
  console.log("Running chat analyzer before clearing logs...");

  const pythonProcess = spawn("python", [
    path.join(__dirname, "chat_analyzer.py"),
  ]);

  // Optional: Capture output and error data
  pythonProcess.stdout.on("data", (data) => {
    console.log(`Python Output: ${data.toString()}`);
  });

  pythonProcess.stderr.on("data", (data) => {
    console.error(`Python Error: ${data.toString()}`);
  });

  // When the Python process finishes
  pythonProcess.on("close", (code) => {
    if (code === 0) {
      // Clear the CSV file by writing the header only
      fs.writeFileSync(
        logFile,
        "Group Name,Sender Name,Message,Phone Number,Date,Time\n"
      );
      console.log("Python analysis successful. Old messages cleared. Starting fresh...");
    } else {
      console.error("Python analysis failed. CSV log file not cleared.");
    }
  });
}

// Function to write a message to the file
function logMessageToFile(data) {
  fs.appendFileSync(logFile, data + "\n");
}

// When the client is ready
client.on("ready", () => {
  console.log("Client is ready!");

  // Create CSV file with headers if it doesn't exist
  if (!fs.existsSync(logFile)) {
    logMessageToFile("Group Name,Sender Name,Message,Phone Number,Date,Time");
  }

  // Print column headers to console for readability
  const headers = `${"Group Name".padEnd(25)} ${"Sender Name".padEnd(
    20
  )} ${"Message".padEnd(30)} ${"Phone Number"} ${"Date".padEnd(12)} ${"Time".padEnd(10)}`;
  console.log(headers);
  console.log("-".repeat(120)); // Separator line

  // Set interval to attempt clearing file (which now runs Python analysis first) every 30 minutes to avoid excessive file size
  setInterval(clearLogFile, 30 * 60 * 1000);
});

// Format and log messages to the CSV file
async function formatAndLogMessage(message) {
  const chat = await message.getChat();
  const sender = await message.getContact();
  
  // Create a date object from the timestamp
  const dateObj = new Date(message.timestamp * 1000);
  
  // Format date and time separately
  const date = dateObj.toLocaleDateString();
  const time = dateObj.toLocaleTimeString();
  
  const phoneNumber = sender.id._serialized.split("@")[0];
  const senderName = sender.pushname || sender.name || "Unknown";

  // Sanitize message body to avoid breaking CSV formatting
  const sanitizedMessageBody = message.body
    .replace(/[\n\r]/g, " ")
    .replace(/,/g, "");

  // Update console output to include separate date and time
  const formattedMessage = `${chat.name.padEnd(25)} ${senderName.padEnd(
    20
  )} ${sanitizedMessageBody.padEnd(30)} ${phoneNumber} ${date.padEnd(12)} ${time.padEnd(10)}`;

  // Update CSV format with separate date and time columns
  const csvFormattedMessage = `${chat.name},${senderName},${sanitizedMessageBody},${phoneNumber},${date},${time}`;

  console.log(formattedMessage); // Log formatted message to console
  logMessageToFile(csvFormattedMessage); // Append CSV-formatted message to file
}

// Specify the group IDs from which you want to log messages
const groupId1 = "120363049123372020@g.us"; // CNG Dispatch Group
const groupId2 = "120363320479571887@g.us"; // Wasil CNG Group
const groupId3 = "120363315079438311@g.us"; // Tempo CNG Group
const groupId4 = "120363147330091953@g.us"; // Splendor CNG Group
const groupId5 = "120363118669828226@g.us"; // NigaChem CNG Group

// Commented the following groups out as they are only test groups
// const groupId6 = "120363038696335071@g.us"; // Heirs Energy PNG Group
// const groupId7 = "2347032132002-1576913526@g.us"; // CHGC Info Centre Group
// const groupId8 = "120363409083699079@g.us"; // Whatsapp bot test Group

// Listen only for messages in the specified groups
client.on("message", async (message) => {
  if (message.from === groupId1 || message.from === groupId2 || message.from === groupId3 || message.from === groupId4 || message.from === groupId5)  {
    await formatAndLogMessage(message);
  }
});

// Start the client
client.initialize();
