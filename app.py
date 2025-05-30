from flask import Flask, request, jsonify
import os
import requests
from retry import retry
from dotenv import load_dotenv

app = Flask(__name__, static_folder='.', static_url_path='')
load_dotenv()

# API Configuration for OpenRouter (ChatGPT and DeepSeek)
API_CONFIG = {
    'deepseek': {
        'url': 'https://openrouter.ai/api/v1/chat/completions',
        'headers': lambda: {
            'Authorization': f'Bearer {os.getenv("OPENROUTER_API_KEY")}',
            'Content-Type': 'application/json',
            'HTTP-Referer': os.getenv('RENDER_EXTERNAL_HOSTNAME', 'https://your-app-name.onrender.com'),
            'X-Title': 'Free AI Chatbot'
        },
        'model': 'deepseek/r-1',
    },
    'chatgpt': {
        'url': 'https://openrouter.ai/api/v1/chat/completions',
        'headers': lambda: {
            'Authorization': f'Bearer {os.getenv("OPENROUTER_API_KEY")}',
            'Content-Type': 'application/json',
            'HTTP-Referer': os.getenv('RENDER_EXTERNAL_HOSTNAME', 'https://your-app-name.onrender.com'),
            'X-Title': 'Free AI Chatbot'
        },
        'model': 'openai/gpt-3.5-turbo',
    },
}

@retry(tries=3, delay=1, backoff=2)
def call_api(ai, message):
    config = API_CONFIG.get(ai)
    if not config:
        return {'error': 'Invalid AI model selected'}

    if not os.getenv("OPENROUTER_API_KEY"):
        return {'error': 'OpenRouter API key is missing. Please configure it.'}

    payload = {
        'model': config['model'],
        'messages': [{'role': 'user', 'content': message}],
        'temperature': 1.0,
    }

    try:
        response = requests.post(config['url'], json=payload, headers=config['headers']())
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.RequestException as e:
        return {'error': f'API call failed for {ai}: {str(e)}'}

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '')
    ai = data.get('ai', 'deepseek')

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    response = call_api(ai, message)
    if isinstance(response, dict) and 'error' in response:
        return jsonify(response), 500
    return jsonify({'response': response})

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)