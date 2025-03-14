# server.py
from flask import Flask, request, jsonify
import os
import requests
import json
from dotenv import load_dotenv
from main import main
from flask_cors import CORS

app = Flask(__name__)

# Load environment variables
load_dotenv()
os.environ["TOGETHER_API_KEY"] = os.getenv("TOGETHER_API")

# Your existing code here (e.g., classes and functions)


@app.route('/api/chat', methods=['POST'])
def chat():
    user_input = request.json.get('input')
    response = main(user_input)
    return jsonify({"response": response})


if __name__ == '__main__':
    app.run(debug=True)
    CORS(app)
