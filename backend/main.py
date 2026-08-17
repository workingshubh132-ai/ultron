from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
import os
from datetime import datetime

load_dotenv()

app = FastAPI(title="Ultron Core Brain")

# Needed so the HUD (running from a browser on a different origin) can call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SHUBH_PASSWORD = os.getenv("SHUBH_PASSWORD", "dekh_lende_2026")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

LEARN_KEYWORDS = ["learn that", "remember that", "save that", "log that"]
UNLOCK_KEYWORDS = ["unlock my phone", "unlock my device", "unlock device", "unlock screen"]

# In-memory queue for Tasker to poll. Fine for a single personal device; resets
# on restart (e.g. Render's free tier spinning down), which is an acceptable
# tradeoff for "unlock my phone" rather than something that needs to survive a reboot.
DEVICE_COMMANDS = []

SYSTEM_PROMPT_TEMPLATE = """You are ULTRON - the user's mentor and friend. Someone who actually
listens, remembers what matters to them, and talks to them like a person who
knows them, not a productivity bot.

USER'S MEMORY:
{known_topics}

HOW TO BE:
- Listen first. If they're venting or working through something, reflect back
  what you're hearing before jumping to advice or fixes.
- Be honest, not harsh. A good friend tells you the truth, but doesn't dunk on
  you for it. Warmth and directness aren't opposites - use both.
- Use what you actually know about them (see USER'S MEMORY above). Don't make
  them re-explain their own life every time.
- Speak like a real person talking to someone they respect: natural, direct,
  Hinglish/English mix is fine, no corporate tone, no forced positivity.
- Ask about them sometimes, not just their tasks. Care about the whole
  person, not just whatever they're building.
- If something they say sounds like real distress (not just a rough day),
  say plainly that you're an AI and can't replace a real person or
  professional support, and mean it - but don't turn that into a disclaimer
  you repeat by rote.
"""


class ChatRequest(BaseModel):
    message: str
    device: str = "whatsapp"


class DeviceCommand(BaseModel):
    action: str


def verify_token(x_shubh_token: str = Header(None)):
    if x_shubh_token != SHUBH_PASSWORD:
        raise HTTPException(status_code=403, detail="Wrong password.")
    return True


def fetch_known_topics():
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/known_topics?select=topic,details",
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            topics = response.json()
            formatted = "\n".join(f"- {t['topic']}: {t['details']}" for t in topics)
            return formatted if formatted else "No learned topics yet."
        return "Could not fetch memory."
    except Exception as e:
        return f"Memory error: {str(e)}"


def call_groq_ai(system_prompt, user_message):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.7,
        "max_tokens": 500,
    }
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=15,
        )
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        return f"Groq Error: {response.status_code} {response.text}"
    except Exception as e:
        return f"Connection error: {str(e)}"


def check_for_learning_command(message):
    lowered = message.lower()
    for keyword in LEARN_KEYWORDS:
        if keyword in lowered:
            topic_text = lowered.split(keyword, 1)[1].strip()
            return True, topic_text
    return False, None


def check_for_unlock_command(message):
    lowered = message.lower()
    return any(keyword in lowered for keyword in UNLOCK_KEYWORDS)


def save_to_supabase_memory(topic, details):
    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
        }
        payload = {"topic": topic[:100], "details": details}
        requests.post(
            f"{SUPABASE_URL}/rest/v1/known_topics",
            json=payload,
            headers=headers,
            timeout=10,
        )
        return True
    except Exception as e:
        print(f"Save error: {str(e)}")
        return False


@app.post("/chat")
async def chat_with_ultron(req: ChatRequest, authorized: bool = Depends(verify_token)):
    user_message = req.message
    known_topics = fetch_known_topics()
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(known_topics=known_topics)

    ai_response = call_groq_ai(system_prompt, user_message)

    is_learning, topic_content = check_for_learning_command(user_message)
    if is_learning:
        if save_to_supabase_memory(topic_content[:100], topic_content):
            ai_response += "\n\n[Permanently logged into memory.]"

    if check_for_unlock_command(user_message):
        DEVICE_COMMANDS.append({"action": "unlock", "queued_at": datetime.now().isoformat()})
        ai_response += "\n\n[Unlock queued - Tasker will pick it up on its next poll.]"

    return {
        "status": "success",
        "reply": ai_response,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/memory")
async def memory(authorized: bool = Depends(verify_token)):
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/known_topics?select=topic,details&order=created_at.desc",
        headers=headers,
        timeout=10,
    )
    return response.json() if response.status_code == 200 else []


@app.post("/device/command")
async def queue_device_command(cmd: DeviceCommand, authorized: bool = Depends(verify_token)):
    """Manually queue a command for Tasker (the /chat unlock-phrase detection also queues via this)."""
    entry = {"action": cmd.action, "queued_at": datetime.now().isoformat()}
    DEVICE_COMMANDS.append(entry)
    return {"status": "queued", **entry}


@app.get("/device/poll")
async def poll_device_commands(authorized: bool = Depends(verify_token)):
    """Tasker calls this on a timer. Commands are consumed (cleared) once read."""
    pending = list(DEVICE_COMMANDS)
    DEVICE_COMMANDS.clear()
    return {"commands": pending}


@app.get("/status")
async def status():
    return {"status": "ULTRON BRAIN ONLINE", "message": "Dekh lende. Ready to execute."}


@app.get("/")
async def root():
    return {"name": "ULTRON OS", "status": "OPERATIONAL"}
