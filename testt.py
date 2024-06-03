from flask import Flask, request, render_template, jsonify
import os
import requests

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Set up your Azure OpenAI API credentials
api_key = os.getenv('AZURE_OPENAI_API_KEY')
api_base_url = os.getenv('AZURE_OPENAI_ENDPOINT')

# API version and deployment ID
api_version = '2022-12-01'
deployment_id = 'ver01'
api_url = f"{api_base_url}/openai/deployments/{deployment_id}/completions?api-version={api_version}"

def get_openai_response(prompt, input_text):
    payload = {
        "prompt": f"{prompt}\n\nInput: {input_text}\n\nOutput:",
        "max_tokens": 300,
        "temperature": 0.7,
        "top_p": 1.0,
        "n": 1,
        "stop": ["\n"]
    }
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        completion = response.json()

        if "choices" in completion and len(completion["choices"]) > 0:
            return completion["choices"][0]["text"].strip()
        else:
            print("Unexpected response format:", completion)
            return None
    except requests.RequestException as e:
        print("Request failed:", e)
        if e.response is not None:
            print("Response status code:", e.response.status_code)
            print("Response content:", e.response.text)
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    question = request.form['question']
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        document_text = read_document(file_path)
        answer = get_openai_response("Answer the following question from the document within two sentences:", f"{question}\n\n{document_text}")
        os.remove(file_path)  # Clean up the file after processing
        return jsonify({'answer': answer})

def read_document(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        document_text = file.read()
    return document_text

if __name__ == '__main__':
    app.run(debug=True)
