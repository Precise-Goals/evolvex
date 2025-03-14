from dotenv import load_dotenv
import os

load_dotenv()

api = os.getenv("TOGETHER_API")
print(api)