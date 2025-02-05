const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

// Initialize the WhatsApp client
const client = new Client({
    authStrategy: new LocalAuth(), // Saves session to avoid scanning QR code every time
    puppeteer: { headless: true }   // Runs without opening a browser window
});

// Generate and display the QR code for authentication
client.on('qr', qr => {
    console.log('Scan this QR code in WhatsApp:');
    qrcode.generate(qr, { small: true });
});

// When the client is ready
client.on('ready', () => {
    console.log('Client is ready!');
});


//Get all WhatsApp messages.
// client.on('message', message => {
//     console.log(`Group ID: ${message.from} ${message.body}`);
// });

const groupId1 = 'xxxxxxxxxxxxxxx@g.us';  // Replace with actual group ID
const groupId2 = 'xxxxxxxxxxxxxxx@g.us';  // Replace with actual group ID

//Get specific WhatsApp messages.
client.on('message', async message => {
    chat = await message.getChat()
    const sender = await message.getContact(); // Fetch sender's contact details
    const timestamp = new Date(message.timestamp * 1000).toLocaleString(); // Converts to local date & time
    const phoneNumber = sender.id._serialized.split('@')[0]; // Extract users number

    if (message.from === groupId1 || message.from === groupId2) {
        console.log(`${chat.name}: [${timestamp}] ${phoneNumber}: ${message.body}: ${sender.name}`);
    }
});

// Start the client
client.initialize();
