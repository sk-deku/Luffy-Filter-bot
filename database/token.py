import pymongo
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "luffy_filter_bot"

class TokenManager:
    def __init__(self):
        self.client = pymongo.MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.users = self.db["users"]

    def add_user(self, user_id):
        """Adds a new user to the database with 0 tokens if they don't exist."""
        if not self.users.find_one({"user_id": user_id}):
            self.users.insert_one({"user_id": user_id, "tokens": 0})

    def update_tokens(self, user_id, amount):
        """Updates user tokens by adding/subtracting a specified amount."""
        self.users.update_one({"user_id": user_id}, {"$inc": {"tokens": amount}}, upsert=True)

    def get_tokens(self, user_id):
        """Retrieves the number of tokens a user has."""
        user = self.users.find_one({"user_id": user_id})
        return user["tokens"] if user else 0

    def deduct_token(self, user_id):
        """Deducts 1 token if the user has enough tokens."""
        user = self.users.find_one({"user_id": user_id})
        if user and user["tokens"] > 0:
            self.update_tokens(user_id, -1)
            return True
        return False
