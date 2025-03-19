import pymongo
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "luffy_filter_bot"

class DB:
    def __init__(self):
        self.client = pymongo.MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.files = self.db["files"]
        self.users = self.db["users"]

    def add_file(self, file_id, file_name, file_size, file_type):
        """Adds a file entry to the database"""
        self.files.insert_one({
            "file_id": file_id,
            "file_name": file_name,
            "file_size": file_size,
            "file_type": file_type
        })

    def get_file(self, file_name):
        """Fetches a file by name"""
        return self.files.find_one({"file_name": file_name})

    def add_user(self, user_id):
        """Adds a new user if not exists"""
        if not self.users.find_one({"user_id": user_id}):
            self.users.insert_one({"user_id": user_id, "tokens": 0})

    def update_tokens(self, user_id, amount):
        """Updates user tokens"""
        self.users.update_one({"user_id": user_id}, {"$inc": {"tokens": amount}})

    def get_tokens(self, user_id):
        """Returns the number of tokens a user has"""
        user = self.users.find_one({"user_id": user_id})
        return user["tokens"] if user else 0

