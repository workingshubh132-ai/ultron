require('dotenv').config();
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

const BACKEND_URL = process.env.BACKEND_URL;
const SHUBH_TOKEN = process.env.SHUBH_TOKEN;
const MY_NUMBER = process.env.MY_NUMBER; // format: "919876543210@c.us"

if (!BACKEND_URL || !SHUBH_TOKEN || !MY_NUMBER) {
  console.error('Missing BACKEND_URL, SHUBH_TOKEN, or MY_NUMBER — copy .env.example to .env and fill it in.');
  process.exit(1);
}

const client = new Client({ authStrategy: new LocalAuth() });

client.on('qr', (qr) => {
  qrcode.generate(qr, { small: true });
  console.log('Scan this QR code with the Ultron WhatsApp account (Linked Devices).');
});

client.on('ready', () => {
  console.log('Ultron WhatsApp Bridge is ONLINE');
});

client.on('message', async (msg) => {
  if (msg.from !== MY_NUMBER) return;

  try {
    console.log(`Received: ${msg.body}`);
    const response = await axios.post(
      `${BACKEND_URL}/chat`,
      { message: msg.body, device: 'whatsapp' },
      { headers: { 'x-shubh-token': SHUBH_TOKEN } }
    );
    await msg.reply(response.data.reply);
    console.log(`Replied: ${response.data.reply.substring(0, 50)}...`);
  } catch (err) {
    await msg.reply('Brain error. Trying again...');
    console.log('Error:', err.message);
  }
});

client.initialize();
