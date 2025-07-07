from flask import Flask, request, jsonify
import subprocess
import base64
from urllib.parse import unquote, unquote_plus

app = Flask(__name__)

# Define a simple password
PASSWORD = "my_secret_password"

def parse(raw):
    # 对Base64编码的字符串进行解码
    decoded_bytes = base64.b64decode( raw )

    # 对URI编码的字符串进行解码
    res = unquote(decoded_bytes)

    return res


@app.route('/clipboard', methods=['GET'])
def clipboard():
    # Get password and text from query string
    password = request.args.get('password')
    text = request.args.get('text')

    # Check if password is provided and correct
    if not password or password != PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401

    # Check if text is provided
    if not text:
        return jsonify({"error": "No text provided"}), 400

    text = parse( text )

    # Write text to clipboard using xclip
    try:
        subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode(), check=True)
    except subprocess.CalledProcessError:
        return jsonify({"error": "Failed to copy text to clipboard"}), 500

    return jsonify({"success": True, "message": "Text copied to clipboard with GET method."})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

