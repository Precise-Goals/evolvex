# server.py
from flask import Flask, request, jsonify
from main import main
from flask_cors import CORS  # Add CORS for cross-origin requests

app = Flask(__name__)
CORS(app)  # Allow frontend to access backend from a different domain


@app.route('/api/code', methods=['POST'])
def chat():
    try:
        user_input = request.json.get('input')  # Matches frontend payload
        response = main(user_input)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)  # Production-ready
