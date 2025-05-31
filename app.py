from flask import Flask, request, jsonify, send_from_directory
import os
import requests
from retry import retry
from dotenv import load_dotenv
from openai import OpenAI

app = Flask(__name__, static_folder='.', static_url_path='')
load_dotenv()

# Initialize OpenAI client with OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

@app.route('/debug-files')
def debug_files():
    files = os.listdir('.')
    return jsonify(files)

@app.route('/')
def serve_index():
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in current directory: {os.listdir('.')}")
    if os.path.exists('index.html'):
        print("index.html found, serving file")
        return send_from_directory('.', 'index.html')
    else:
        print("index.html not found")
        return "index.html not found", 404

@retry(tries=3, delay=1, backoff=2)
def call_api(message):
    try:
        print(f"Sending request with message: {message}")
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": os.getenv('RENDER_EXTERNAL_HOSTNAME', 'https://nazmul-ai-chatbot.onrender.com'),
                "X-Title": "Free AI Chatbot"
            },
            extra_body={},
            model="google/gemma-3n-e4b-it:free",
            messages=[
                {"role": "user", "content": message}
            ]
        )
        print(f"Received response: {completion.choices[0].message.content}")
        return completion.choices[0].message.content
    except Exception as e:
        return {'error': f'API call failed: {str(e)}'}

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '')
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    response = call_api(message)
    if isinstance(response, dict) and 'error' in response:
        return jsonify(response), 500
    return jsonify({'response': response})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)