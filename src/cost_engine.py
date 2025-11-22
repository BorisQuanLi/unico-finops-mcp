import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class CostArchitect:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-3-pro-preview')
        else:
            print("⚠️ WARNING: GEMINI_API_KEY not found. AI features disabled.")
            self.model = None

    def analyze_terraform(self, tf_content: str, cloud_metrics: str = ""):
        if not self.model:
            return "AI Analysis Unavailable (Missing Key)."

        prompt = f"""
        You are a Senior FinOps Engineer. Analyze this Terraform code.
        
        TERRAFORM:
        {tf_content}

        METRICS:
        {cloud_metrics}

        Identify waste and suggest specific Terraform changes.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"AI Error: {str(e)}"