import os
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Load secrets
load_dotenv()

class FinOpsDB:
    def __init__(self):
        self.uri = os.getenv("MONGODB_URI")
        # Handle case where URI is missing (common in dev)
        if not self.uri:
            print("⚠️ WARNING: MONGODB_URI not found in .env. Using mock DB.")
            self.db = None
            return

        try:
            self.client = MongoClient(self.uri)
            self.db = self.client[os.getenv("DB_NAME", "unico_finops")]
            self.history_col = self.db["optimization_history"]
        except Exception as e:
            print(f"⚠️ DB Connection Error: {e}")
            self.db = None

    def log_analysis(self, resource_id: str, suggestion: str, savings_est: float):
        """Saves an optimization suggestion to MongoDB."""
        if self.db is None: return None
        
        record = {
            "resource_id": resource_id,
            "suggestion": suggestion,
            "estimated_monthly_savings": savings_est,
            "timestamp": datetime.datetime.utcnow(),
            "status": "PROPOSED"
        }
        return self.history_col.insert_one(record).inserted_id

    def check_history(self, resource_id: str):
        """Checks if we have already optimized this resource."""
        if self.db is None: return None
        return self.history_col.find_one({"resource_id": resource_id})