from pymongo import MongoClient

class Database:
    def __init__(self, mongo_uri):
        self.client = MongoClient(mongo_uri)
        self.db = self.client["AutoFilterBot"]
        self.files = self.db["files"]
        self.users = self.db["users"]

    def search_files(self, query):
        return list(self.files.find({"file_name": {"$regex": query, "$options": "i"}}))

    def add_file(self, file_id, file_name):
        if not self.files.find_one({"file_id": file_id}):
            self.files.insert_one({"file_id": file_id, "file_name": file_name})

    def get_tokens(self, user_id):
        user = self.users.find_one({"user_id": user_id})
        return user.get("tokens", 0) if user else 0  # Safe retrieval

    def add_tokens(self, user_id, amount):
        self.users.update_one({"user_id": user_id}, {"$inc": {"tokens": amount}}, upsert=True)

    def deduct_token(self, user_id, amount):
        user = self.users.find_one({"user_id": user_id})
        if user and user.get("tokens", 0) >= amount:  # Safe token check
            self.users.update_one({"user_id": user_id}, {"$inc": {"tokens": -amount}})
            return True
        return False
