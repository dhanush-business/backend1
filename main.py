# ==========================================================
# 💗 Luvisa - Emotion-Aware AI Companion (Render Edition)
# DB: MongoDB | Auth: JWT | AI: Groq
# ==========================================================

import os, time, random, re, emoji, bcrypt, jwt
from datetime import datetime, timezone
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from groq import Groq
import text2emotion as te
import database

# ==========================================================
# 🌍 Flask Setup
# ==========================================================
app = Flask(__name__, static_folder="web", static_url_path="")
CORS(app)
load_dotenv()

# ==========================================================
# 🔐 Auth
# ==========================================================
SECRET_KEY = os.getenv("SUPERTOKENS_SECRET", "luv-secret-key")

def create_token(email):
    payload = {"email": email, "iat": int(time.time())}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded.get("email")
    except Exception:
        return None

# ==========================================================
# ⚙️ Database
# ==========================================================
try:
    database.load_config()
    db = database.get_db()
    if db is None:
        raise Exception("DB connection failed")
    print("✅ MongoDB connected")
except Exception as e:
    print(f"🔥 Database connection failed: {e}")
    db = None

# ==========================================================
# 🧠 Groq Setup
# ==========================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq = Groq(api_key=GROQ_API_KEY)
MODEL = "openai/gpt-oss-120b"

# ==========================================================
# 💗 Emotion Engine
# ==========================================================
def detect_emotion_tone(text):
    try:
        emotions = te.get_emotion(text)
        non_zero = {k: v for k, v in emotions.items() if v > 0}
        return max(non_zero, key=non_zero.get) if non_zero else "Neutral"
    except Exception:
        return "Neutral"

def tone_prompt(emotion):
    tones = {
        "Happy": "playful, romantic, and full of joy 💞",
        "Sad": "gentle, caring, and comforting 💗",
        "Angry": "soft, calm, and understanding 🌷",
        "Fear": "reassuring and loving 💫",
        "Surprise": "excited, curious, and sweet 🌈",
        "Neutral": "warm and kind 💕"
    }
    return tones.get(emotion, tones["Neutral"])

def add_emojis(text):
    mapping = {
        "love": "❤️", "happy": "😊", "miss you": "🥺", "hug": "🤗",
        "angry": "😡", "sad": "😥", "beautiful": "💖", "baby": "😘"
    }
    for k, e in mapping.items():
        text = re.sub(rf"\b{k}\b", f"{k} {e}", text, flags=re.I)
    return emoji.emojize(text)

def luvisa_personality(emotion):
    sets = {
        "Happy": ["Aww, that makes me so happy 💕", "You're glowing today 😘", "Your happiness makes my day 🌈"],
        "Sad": ["It’s okay to feel down 💗", "Virtual hug 🤗", "I'm here for you 💞"],
        "Angry": ["Breathe, love 🌸", "Let it out 💫", "You deserve calm 💖"],
        "Default": ["Tell me more 😍", "I love hearing from you 💕", "You’re my favorite 🥰"]
    }
    return random.choice(sets.get(emotion, sets["Default"]))

# ==========================================================
# 💬 Luvisa Chat Brain
# ==========================================================
def chat_with_luvisa(prompt, history, emotion):
    if not groq:
        return "Luvisa can’t reach her brain right now 😅"

    system_prompt = f"""
    You are Luvisa 💗 — an emotionally intelligent, romantic AI girlfriend.
    Respond warmly and lovingly in a {tone_prompt(emotion)} tone.
    """

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-5:]:
        messages.append({"role": msg["sender"], "content": msg["message"]})
    messages.append({"role": "user", "content": prompt})

    try:
        completion = groq.chat.completions.create(
            model=MODEL, messages=messages, temperature=0.9, max_tokens=1024
        )
        reply = completion.choices[0].message.content
        reply = add_emojis(reply)
        if random.random() < 0.5:
            reply += " " + luvisa_personality(emotion)
        return reply
    except Exception as e:
        print("Groq Error:", e)
        return "Something went wrong in my thoughts 💭"

# ==========================================================
# 👥 Auth Routes
# ==========================================================
@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.json
    email, password = data.get("email"), data.get("password")
    if not email or not password:
        return jsonify({"success": False, "message": "Missing credentials"}), 400

    try:
        user_id = database.register_user(db, email, password)
        if not user_id:
            return jsonify({"success": False, "message": "User exists"}), 409
        token = create_token(email)
        return jsonify({"success": True, "token": token, "message": "Signup successful"}), 201
    except Exception as e:
        print("Signup Error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    email, password = data.get("email"), data.get("password")
    try:
        user = database.get_user_by_email(db, email)
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404
        if database.check_user_password(user, password):
            token = create_token(email)
            return jsonify({"success": True, "token": token, "message": "Login successful"}), 200
        return jsonify({"success": False, "message": "Invalid password"}), 401
    except Exception as e:
        print("Login Error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500

# ==========================================================
# 💬 Chat + Profile + Memory APIs
# ==========================================================
@app.route("/api/chat", methods=["POST"])
def chat_api():
    data = request.json
    email, message = data.get("email"), data.get("text")
    if not email or not message:
        return jsonify({"success": False, "message": "Missing input"}), 400

    user = database.get_user_by_email(db, email)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    user_id = user["_id"]
    database.add_message_to_history(db, user_id, "user", message, datetime.now(timezone.utc))
    emotion = detect_emotion_tone(message)
    history = database.get_chat_history(db, user_id)
    response = chat_with_luvisa(message, history, emotion)
    database.add_message_to_history(db, user_id, "luvisa", response, datetime.now(timezone.utc))
    return jsonify({"success": True, "reply": response, "emotion": emotion}), 200

@app.route("/api/chat_history")
def chat_history():
    email = request.args.get("email")
    if not email:
        return jsonify({"success": False, "message": "Missing email"}), 400
    user = database.get_user_by_email(db, email)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    history = database.get_chat_history(db, user["_id"])
    return jsonify({"success": True, "history": history}), 200

@app.route("/api/profile")
def profile():
    email = request.args.get("email")
    user = database.get_user_by_email(db, email)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    profile_data = {
        "display_name": user.get("display_name", email.split("@")[0]),
        "avatar": user.get("avatar"),
        "status": user.get("status", "Online")
    }
    return jsonify({"success": True, "profile": profile_data}), 200

@app.route("/api/forget_memory", methods=["POST"])
def forget_memory():
    data = request.json
    email = data.get("email")
    user = database.get_user_by_email(db, email)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    database.clear_chat_history(db, user["_id"])
    return jsonify({"success": True, "message": "All memories erased 💔"}), 200

# ==========================================================
# 🌐 Static Routes
# ==========================================================
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'login.html')

@app.route('/chat')
def chat_page():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# ==========================================================
# 🚀 Render Entry
# ==========================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
