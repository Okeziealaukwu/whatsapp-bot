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
// const logFile = "chat_logs.txt"; // File to save chat messages in text file

// Generate and display the QR code for authentication
client.on("qr", (qr) => {
  console.log("Scan this QR code in WhatsApp:");
  qrcode.generate(qr, { small: true });
});

// Function to clear file every hour
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

  const headers = `${"Group Name".padEnd(25)} ${"Sender Name".padEnd(
    20
  )} ${"Message".padEnd(30)} ${"Phone Number"} ${"Time Stamp".padEnd(22)}`;

  //Clear csv
  if (!fs.existsSync(logFile)) {
    logMessageToFile("Group Name,Sender Name,Message,Phone Number,Time Stamp");
  }

  // Print column headers
  console.log(headers);
  console.log("-".repeat(120)); // Separator line for readability

  // Save headers to file use to get clean formatted txt file
  // logMessageToFile(headers);
  // logMessageToFile('-'.repeat(120));

  // Set interval to clear file every hour
  setInterval(clearLogFile, 60 * 60 * 1000);
});

client.on("message", async (message) => {
  console.log("Received message from:", message.from, "Message:", message.body);
});

// Function to format and log message
async function formatAndLogMessage(message) {
  const chat = await message.getChat();
  const sender = await message.getContact(); // Fetch sender's contact details
  const timestamp = new Date(message.timestamp * 1000).toLocaleString(); // Converts to local date & time
  const phoneNumber = sender.id._serialized.split("@")[0]; // Extract user's number
  const senderName = sender.pushname || sender.name || "Unknown";

  // Ensure message body does not break CSV formatting
  const sanitizedMessageBody = message.body
    .replace(/[\n\r]/g, " ")
    .replace(/,/g, "");

  // Proper template literals with backticks
  const formattedMessage = `${chat.name.padEnd(25)} ${senderName.padEnd(
    20
  )} ${sanitizedMessageBody.padEnd(30)} ${phoneNumber} ${timestamp.padEnd(22)}`;

  const csvformattedMessage = `${chat.name},${senderName},${sanitizedMessageBody},${phoneNumber},${timestamp}`;

  console.log(formattedMessage); // Log in console
  logMessageToFile(csvformattedMessage); // Save to file
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

// Function to trigger python script
function runChatAnalyzer() {
  console.log("Running logs...");

  const pythonProcess = spawn("python", [
    path.join(__dirname, "chat_analyzer.py"),
  ]);

  pythonProcess.stdout.on("data", (data) => {
    console.log(`Python Output: ${data.toString()}`);
  });

  pythonProcess.stderr.on("data", (data) => {
    console.error(`Python Error: ${data.toString()}`);
  });

  pythonProcess.on("close", (code) => {
    console.log(`Python script finished with exit code ${code}`);
  });

//   clearLogFile();
}

// Start the client
client.initialize();

// Watch for CSV Changes and Trigger Python

// fs.watch(logFile, (eventType, filename) => {
//   if (eventType === "change") {
//     console.log("New chat logs detected. Running analyzer...");
//     runChatAnalyzer();
//   }
// });
