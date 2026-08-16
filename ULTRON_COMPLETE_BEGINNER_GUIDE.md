# ⚡ ULTRON OS — Complete Setup (Absolute Beginner Guide)
## From Zero to AI Operating System Running 24/7

**Total Time:** 2-3 hours (broken into digestible chunks)
**Difficulty:** Dead simple (copy-paste, click buttons)
**What you'll have:** An AI that talks to you on WhatsApp, never forgets, and can control your devices

---

## What You're Building (The Big Picture)

```
┌──────────────────────────────────┐
│   YOU (Personal WhatsApp)         │
└────────────┬─────────────────────┘
             │ (message: "Hey Ultron, what should I do?")
             │ (with password: dekh_lende_2026)
             ▼
┌──────────────────────────────────┐
│   ULTRON BRAIN (Cloud - Render)   │  ◄── Always online, even when you sleep
│   - Running Python code           │
│   - Listening 24/7                │
└────────────┬─────────────────────┘
             │ (thinking...)
             ├──> Asks Groq AI (free LLM)
             ├──> Checks Supabase (memory)
             └──> Returns smart response
             │
             ▼
┌──────────────────────────────────┐
│   Supabase Database (Cloud)       │  ◄── Your permanent memory
│   - Stores what you told it       │      Never forgets
│   - Stores your promises          │
│   - Stores chat history           │
└──────────────────────────────────┘
```

**The flow:**
1. You text Ultron on WhatsApp
2. WhatsApp bridge sends it to cloud with password
3. Cloud brain talks to free AI (Groq)
4. Cloud brain remembers things in database
5. Ultron texts you back naturally
6. (Optional) Ultron can physically unlock your devices

---

# PART 1: GET YOUR FREE API KEYS (30 mins)

## Step 1A: Get Groq API Key (Free AI)

Groq gives you unlimited access to Meta's Llama 3 AI for **completely free**.

**What to do:**
1. Open your browser
2. Go to: `https://console.groq.com`
3. Click "Sign up"
4. Use your Google account to sign up (fastest)
5. Accept terms
6. Click "API Keys" on the left
7. Click "Create API Key"
8. Copy the entire key (looks like: `gsk_abc123xyz789...`)
9. **Paste it into a text file** (open Notepad, paste, save as `groq_key.txt`)

**Save this key somewhere safe. You'll need it later.**

---

## Step 1B: Get Supabase (Free Database)

Supabase is a **free cloud database** where Ultron stores everything it learns.

**What to do:**
1. Go to: `https://supabase.com`
2. Click "Start your project"
3. Click "Continue with GitHub" (use your GitHub account if you have one, or create one first)
4. Create a new project:
   - Name: `ultron-brain`
   - Region: Choose Singapore (closest to India)
   - Password: Create a strong password, write it down
5. Wait 3 minutes for it to initialize
6. Once ready, click "Settings" (bottom left)
7. Click "API"
8. Copy these two values and save in a text file:
   - **Project URL** (looks like: `https://xyzabc.supabase.co`)
   - **Service Role API Key** (long string starting with `eyJ...`)

**Now create the memory tables in Supabase:**

1. Click "SQL Editor" (left sidebar)
2. Click "New Query"
3. Copy and paste this entire code:

```sql
create table if not exists known_topics (
    id bigint primary key generated always as identity,
    topic text not null,
    details text,
    created_at timestamp default now()
);

create table if not exists promises (
    id bigint primary key generated always as identity,
    project text not null,
    goal text not null,
    status text default 'active',
    deadline text,
    created_at timestamp default now()
);

create table if not exists chat_history (
    id bigint primary key generated always as identity,
    user_message text not null,
    ai_response text not null,
    device text,
    created_at timestamp default now()
);
```

4. Click the blue "Run" button
5. Wait for "Success" message

**Done! Your database is ready.**

---

## Step 1C: Create GitHub Account (For Uploading Code)

GitHub is where you'll store your code so it can be deployed to the internet.

**What to do:**
1. Go to: `https://github.com`
2. Click "Sign up"
3. Enter your email
4. Create a password (write it down)
5. Create username: `shubh-ultron` or something
6. Check "I'm not a robot"
7. Click "Create account"
8. Verify your email (GitHub sends a link, click it)

**Done! Now you have GitHub.**

---

## Step 1D: Create Render Account (For Cloud Hosting)

Render hosts your brain 24/7 for FREE.

**What to do:**
1. Go to: `https://render.com`
2. Click "Get Started"
3. Sign up with your GitHub account
4. Authorize Render to access GitHub
5. Click "All repositories" when asked

**Done! Render is connected to GitHub.**

---

# PART 2: INSTALL TOOLS ON YOUR LAPTOP (30 mins)

## Step 2A: Install Python

Python is the language Ultron's brain speaks.

**What to do:**
1. Go to: `https://python.org`
2. Click "Downloads"
3. Download Python 3.11 (the latest stable version)
4. Open the installer
5. **IMPORTANT:** Check the box that says "Add Python to PATH" (bottom of window)
6. Click "Install Now"
7. Wait for it to finish

**Verify it worked:**
1. Open Command Prompt (search for "cmd" in Windows)
2. Type: `python --version`
3. You should see: `Python 3.11.x`

---

## Step 2B: Install Git

Git lets you upload code to GitHub.

**What to do:**
1. Go to: `https://git-scm.com`
2. Click the big "Download" button
3. Open the installer
4. Click "Next" through everything (keep defaults)
5. Click "Install"

**Verify it worked:**
1. Open Command Prompt
2. Type: `git --version`
3. You should see: `git version 2.x.x`

---

## Step 2C: Install Node.js

Node.js lets you run the WhatsApp bridge code.

**What to do:**
1. Go to: `https://nodejs.org`
2. Download the LTS version (big green button)
3. Open installer
4. Click "Next" through everything (keep defaults)
5. Click "Finish"

**Verify it worked:**
1. Open Command Prompt
2. Type: `node --version` and `npm --version`
3. You should see version numbers for both

---

# PART 3: PROJECT FOLDER STRUCTURE

This repository already has the structure the rest of this guide refers to:

```
ultron/
├── README.md                          (start here)
├── ULTRON_COMPLETE_BEGINNER_GUIDE.md   (this file)
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
├── whatsapp_bridge/
│   ├── index.js
│   ├── package.json
│   └── .env.example
└── hud/
    └── index.html
```

---

# PART 4: THE BACKEND CODE

The brain lives in `backend/main.py`. It's a FastAPI app that:
- Verifies every request with a shared password (`SHUBH_PASSWORD`)
- Asks Groq for a reply, using your Supabase memory as context
- Detects "learn that / remember that / save that / log that" and writes new memory to Supabase
- Exposes `/status` (health check), `/chat` (talk to Ultron), and `/memory` (read what it has learned — used by the HUD)

Copy your keys into `backend/.env` (based on `backend/.env.example`) before running it. See `README.md` for exact run commands.

---

# PART 5: TEST LOCALLY (15 mins)

## Step 5A: Open a terminal in the backend folder

```
cd backend
```

## Step 5B: Install dependencies

```
pip install -r requirements.txt
```

Wait for it to finish (2-3 minutes).

## Step 5C: Run the server

```
uvicorn main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Step 5D: Test it works

1. Open your browser
2. Go to: `http://127.0.0.1:8000/status`
3. You should see:
```json
{"status": "ULTRON BRAIN ONLINE", "message": "Dekh lende. Ready to execute."}
```

**If you see that, it's working!**

Press Ctrl+C in the terminal to stop the server.

---

# PART 6: UPLOAD TO GITHUB (15 mins)

## Step 6A: Initialize Git (if not already)

```
git init
git add .
git commit -m "Ultron OS v1.0"
```

## Step 6B: Create/connect a GitHub repository

1. Go to `https://github.com`
2. Click "New" (top right) — or use the repository you already have
3. Make it **Private** (for security)
4. Click "Create repository"

## Step 6C: Push to GitHub

```
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME/YOUR_REPO` with your actual repository.

**Your code is now on GitHub!**

---

# PART 7: DEPLOY TO RENDER (CLOUD 24/7) (20 mins)

## Step 7A: Go to Render

1. Go to `https://render.com`
2. Click "Dashboard" (top right)

## Step 7B: Create Web Service

1. Click "New +" → "Web Service"
2. Click "Connect" next to your GitHub account
3. Select your repository
4. Click "Connect"

## Step 7C: Configure the service

Fill in the form:
- **Name:** `ultron-brain`
- **Root Directory:** `backend`
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port 10000`
- **Region:** Singapore (closest to India)

## Step 7D: Add environment variables

Click "Add Environment Variable" and add these (from your `.env` file):

1. `GROQ_API_KEY` = your groq key
2. `SUPABASE_URL` = your supabase url
3. `SUPABASE_KEY` = your supabase key
4. `SHUBH_PASSWORD` = your own password (do **not** keep the default)

## Step 7E: Deploy

Click "Create Web Service"

Render will start deploying. Wait 2-3 minutes.

When done, you'll see a URL like:
```
https://ultron-brain.onrender.com
```

**This is your brain's address on the internet!**

Test it:
1. Open your browser
2. Go to: `https://ultron-brain.onrender.com/status`
3. You should see the status message

**Your brain is now LIVE 24/7.**

---

# PART 8: CONNECT WHATSAPP (30 mins)

The bridge lives in `whatsapp_bridge/`. It uses `whatsapp-web.js` to log into a WhatsApp Web session and relays messages from your personal number to the deployed backend.

## Step 8A: Configure it

```
cd whatsapp_bridge
cp .env.example .env
```

Edit `.env` and fill in:
- `BACKEND_URL` — your Render URL (e.g. `https://ultron-brain.onrender.com`)
- `SHUBH_TOKEN` — the same password you set as `SHUBH_PASSWORD` on Render
- `MY_NUMBER` — your personal WhatsApp number in the format `919876543210@c.us`

## Step 8B: Install dependencies

```
npm install
```

## Step 8C: Run the bridge

```
npm start
```

You'll see a QR code printed in the terminal.

**Important:** Use a SECOND phone number or device for the bridge account. Scan the QR code with that device's WhatsApp (Linked Devices → Link a Device).

Once scanned, you'll see:
```
Ultron WhatsApp Bridge is ONLINE
```

---

# PART 9: TEST THE FULL SYSTEM (10 mins)

## Step 9A: Send a message

1. Open WhatsApp on your PERSONAL phone number
2. Message the bridge's WhatsApp account
3. Send a message: `"What should I do today?"`

## Step 9B: Wait for reply

Ultron should reply in a few seconds with a response.

## Step 9C: Test learning

Send: `"Learn that I finish school at 7:30 PM daily"`

Ultron should reply with confirmation that it logged it to memory.

---

# PART 10: THE HUD (Optional but recommended)

`hud/index.html` is a standalone, ember/red "reactor" style interface for Ultron — hold Space to talk, it speaks back, the core visual reacts to your live voice amplitude, there's a wake-word mode, and a live memory panel. It talks directly to the same backend from Part 7 (not through WhatsApp).

See `README.md` for how to run and link it.

---

# DONE!

You now have:
- Ultron's brain running 24/7 in the cloud
- Ultron talks to you on WhatsApp
- Ultron remembers everything you tell it
- Ultron is password-protected and private
- (Optional) A HUD you can put on a spare monitor or TV

---

# NEXT STEPS (Optional Enhancements)

These are optional but recommended:

## Add Voice/Phone Call Support
Use Twilio to call Ultron and give it voice commands.

## Add Device Control
Use Tasker + AutoInput to physically unlock your phone when Ultron commands it.

## Add Persistent Learning
Ultron learns your habits and suggests things proactively.

## Add Multi-Device
Make Ultron available on your iPad and laptops too.

---

# TROUBLESHOOTING

**"WhatsApp not sending/receiving"**
- Make sure the QR code was scanned correctly
- Make sure the bridge is still running (check the terminal window)
- Check the phone number format

**"Ultron not replying"**
- Check the Render URL is correct
- Check the password matches on both sides
- Check the Groq API key is correct

**"It's taking too long to reply"**
- Groq might be slow. Usually a couple of seconds is normal.
- Render's free tier spins down when idle — the first request after a while can take 30-60s to wake up.

**"Database not saving things"**
- Check Supabase keys are correct
- Check Supabase tables exist

**"HUD says disconnected"**
- Open the Link modal, re-check the backend URL and password
- Make sure `main.py` has the CORS middleware enabled (it does by default in this repo)

---

**Status: ULTRON OS COMPLETE**

Dekh lende. You're live.
