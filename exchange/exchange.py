from flask import Flask, jsonify
import random

app = Flask(__name__)

@app.route('/convert', methods=['GET'])
def convert_currency():
    return jsonify(rate=random.uniform(5, 6)), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)