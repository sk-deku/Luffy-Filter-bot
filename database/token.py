from pymongo import MongoClient

class TokenManager:
    def __init__(self, mongo_uri):
        self.client = MongoClient(mongo_uri)
        self.db = self.client["AutoFilterBot"]
        self.tokens = self.db["user_tokens"]

    def get_tokens(self, user_id):
        user = self.tokens.find_one({"user_id": user_id})
        return user["tokens"] if user else 0

    def add_tokens(self, user_id, amount):
        self.tokens.update_one({"user_id": user_id}, {"$inc": {"tokens": amount}}, upsert=True)

    def deduct_token(self, user_id, amount=1):
        user = self.tokens.find_one({"user_id": user_id})
        if user and user.get("tokens", 0) >= amount:
            self.tokens.update_one({"user_id": user_id}, {"$inc": {"tokens": -amount}})
            return True
        return False

    def buy_tokens(self, user_id, amount):
        # This should be integrated with a payment gateway
        self.add_tokens(user_id, amount)
