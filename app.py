from flask import Flask, request, jsonify, send_from_directory
import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

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

def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

@app.route('/chat', methods=['POST'])
def chat():
    if 'message' not in request.form and 'image' not in request.files:
        return jsonify({'error': 'No message or image provided'}), 400

    message = request.form.get('message', '')
    image_file = request.files.get('image')

    try:
        if image_file:
            image_base64 = encode_image(image_file)
            payload = {
                "model": "google/gemma-3n-e4b-it:free",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": message} if message else {"type": "text", "text": "Describe this image"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]
                    }
                ]
            }
        else:
            payload = {
                "model": "google/gemma-3n-e4b-it:free",
                "messages": [{"role": "user", "content": message}]
            }

        print(f"Sending payload: {payload}")
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": os.getenv('RENDER_EXTERNAL_HOSTNAME', 'https://nazmul-ai-chatbot.onrender.com'),
                "X-Title": "SPD Bot for Engineers"
            },
            extra_body={},
            **payload
        )
        print(f"Received response: {completion.choices[0].message.content}")
        return jsonify({'response': completion.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': f'API call failed: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)