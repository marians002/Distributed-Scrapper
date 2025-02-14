from flask import Flask, render_template, request, jsonify
import socket
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# SERVER_IP = "10.0.11.2"
SERVER_PORT = 5002
SERVER_IP = "127.0.0.1"


@app.route('/')
def home():
    return render_template('frontend.html')


@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.form['url']
    scrape_option = request.form['scrapeOption']

    settings = {
        'extract_html': scrape_option == 'html',
        'extract_css': scrape_option == 'css',
        'extract_js': scrape_option == 'js'
    }

    response = send_request_to_server(url, settings)
    return jsonify(response)

#region OK
def send_request_to_server(url, settings):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print(SERVER_IP, SERVER_PORT)
        s.connect((SERVER_IP, SERVER_PORT))
        print("Successfully connected")
        request_data = str({'url': url, 'settings': settings})
        s.sendall(request_data.encode())
        print("Waiting for response from server...")

        # Receive the response in parts and concatenate them
        data = b""
        while True:
            part = s.recv(4096)
            if not part:
                break
            data += part

        print("Received response from server")
        return eval(data.decode())


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001)
