from flask import Flask, request, jsonify
from flask_cors import CORS
from main import process_request

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "https://your-app.vercel.app"}})


@app.route('/api/code', methods=['POST'])
def chat():
    try:
        user_input = request.json.get('input')
        if not user_input:
            return jsonify({"error": "No input provided"}), 400
        response = process_request(user_input)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
