"""
setup_database.py — MongoDB version
Creates initial collections and indexes for Luvisa's AI assistant
"""

from pymongo import MongoClient, ASCENDING
from pymongo.server_api import ServerApi
import os

def setup_mongodb():
    """Creates required collections and indexes in MongoDB Atlas."""
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise ValueError("❌ MONGODB_URI environment variable not found. Please set it before running.")

    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client["luvisa_db"]  # Matches your MongoDB database name

    print("⚙️  Connected to MongoDB Atlas successfully.")
    print("🧩 Creating required collections...")

    # 1️⃣ Users collection
    if "users" not in db.list_collection_names():
        db.create_collection("users")
        print("✅ Created 'users' collection.")
    else:
        print("ℹ️  'users' collection already exists.")

    # Add unique index for email
    db.users.create_index([("email", ASCENDING)], unique=True)

    # 2️⃣ Profiles collection
    if "profiles" not in db.list_collection_names():
        db.create_collection("profiles")
        print("✅ Created 'profiles' collection.")
    else:
        print("ℹ️  'profiles' collection already exists.")

    # 3️⃣ Chat history collection
    if "chat_history" not in db.list_collection_names():
        db.create_collection("chat_history")
        print("✅ Created 'chat_history' collection.")
    else:
        print("ℹ️  'chat_history' collection already exists.")

    # Create helpful indexes for faster queries
    db.chat_history.create_index([("user_id", ASCENDING)])
    db.chat_history.create_index([("timestamp", ASCENDING)])

    print("🎉 MongoDB setup complete! Collections are ready:")
    print("   - users")
    print("   - profiles")
    print("   - chat_history")

    client.close()

if __name__ == "__main__":
    setup_mongodb()
