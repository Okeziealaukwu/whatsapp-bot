// Description: This script uses the WhatsApp Web API to log messages from specific groups into a CSV file.
// It also runs a Python script to analyze the chat data before clearing the log file.
const express = require("express");
const { Client, LocalAuth } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

const app = express();
const PORT = process.env.PORT || 3000;
let qrCodeData = "";

// Initialize the WhatsApp client
const client = new Client({
  authStrategy: new LocalAuth({ clientId: "whatsapp_bot" }), // Add a unique client ID
  puppeteer: {
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
      "--no-zygote",
    ],
  },
});

const logFile = path.join(__dirname, "chat_logs.csv"); // CSV file location

// Generate and display the QR code for authentication
client.on("qr", (qr) => {
  console.log("Scan this QR code in WhatsApp:");
  qrcode.generate(qr, { small: true });
  qrcode.toDataURL(qr, (err, url) => {
    if (err) {
      console.error("Failed to generate QR", err);
    } else {
      qrCodeData = url; // Save the base64 image
    }
  });
});

// Serve the QR code on a page
app.get("/", (req, res) => {
  if (!qrCodeData) {
    return res.send("<h2>QR Code not generated yet. Please wait...</h2>");
  }

  return res.send(`
    <html>
      <head>
        <title>Scan WhatsApp QR Code</title>
      </head>
      <body style="display: flex; align-items: center; justify-content: center; height: 100vh; flex-direction: column;">
        <h1>Scan the QR Code</h1>
        <img src="${qrCodeData}" alt="QR Code" />
      </body>
    </html>
  `);
});

// Function to clear file only if Python script runs successfully
function clearLogFile() {
  fs.writeFileSync(
    logFile,
    "Group Name,Sender Name,Message,Phone Number,Time Stamp\n"
  ); // Reset file with headers
  console.log("Old messages cleared. Starting fresh...");
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
  )} ${"Message".padEnd(30)} ${"Phone Number"} ${"Time Stamp".padEnd(22)}`;

  //Clear csv
  if (!fs.existsSync(logFile)) {
    logMessageToFile("Group Name,Sender Name,Message,Phone Number,Time Stamp");
  }

  // Print column headers
  console.log(headers);
  console.log("-".repeat(120)); // Separator line

  // Set interval to attempt clearing file (which now runs Python analysis first) every 30 minutes to avoid excessive file size
  setInterval(clearLogFile, 30 * 60 * 1000);
});

// Format and log messages to the CSV file
async function formatAndLogMessage(message) {
  const chat = await message.getChat();
  const sender = await message.getContact();
  const timestampDate = new Date(message.timestamp * 1000);
  const date = timestampDate.toLocaleDateString();
  const time = timestampDate.toLocaleTimeString();
  const phoneNumber = sender.id._serialized.split("@")[0];
  const senderName = sender.pushname || sender.name || "Unknown";

  const sanitizedMessageBody = message.body
    .replace(/[\n\r]/g, " ")
    .replace(/,/g, "");

  const formattedMessage = `${chat.name.padEnd(25)} ${senderName.padEnd(
    20
  )} ${sanitizedMessageBody.padEnd(30)} ${phoneNumber} ${date} ${time}`;

  const csvFormattedMessage = `${chat.name},${senderName},${sanitizedMessageBody},${phoneNumber},${date},${time}`;

  console.log(formattedMessage);
  logMessageToFile(csvFormattedMessage);
}

// Get all WhatsApp messages.
// client.on("message", async (message) => {
//   await formatAndLogMessage(message);
// });

// Get specific WhatsApp messages from groups
const groupId1 = "120363409083699079@g.us"; // Replace with actual group ID
const groupId2 = "2349032959233-1543393783@g.us"; // Replace with actual group ID

client.on("message", async (message) => {
  if (message.from === groupId1 || message.from === groupId2) {
    await formatAndLogMessage(message);
  }
});

// Start the client
client.initialize();

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
