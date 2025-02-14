from flask import Flask, request, jsonify
from html_fetcher import fetch_html
from DB_manager import fetch_data_from_db, init_db
import socket
import threading

app = Flask(__name__)

# Initialize the database
init_db()


@app.route('/scrape', methods=['POST'])
def scrape_endpoint():
    data = request.json
    urls = data.get('urls', [])
    settings = data.get('settings', {})
    results = scrape(urls, settings)
    return jsonify(results)


def scrape(urls, settings):
    results = {}
    for url in urls:
        # Initialize the result dictionary for the current URL
        results[url] = {}

        # Fetch data from the database if available
        html_content, css_content, js_content = fetch_data_from_db(url)

        # Check if HTML is requested and available in the database
        if settings.get('extract_html', False):
            if html_content:
                results[url]['html'] = html_content[0]
            else:
                # Fetch HTML from the web if not in the database
                html_contents, _ = fetch_html([url], {'extract_html': True})
                results[url]['html'] = html_contents.get(url)

        # Check if CSS is requested and available in the database
        if settings.get('extract_css', False):
            if css_content:
                results[url]['css'] = css_content[0]
            else:
                # Fetch CSS from the web if not in the database
                _, extra_info = fetch_html([url], {'extract_css': True})
                results[url]['css'] = extra_info.get(url, {}).get('css', [])

        # Check if JavaScript is requested and available in the database
        if settings.get('extract_js', False):
            if js_content:
                results[url]['js'] = js_content[0]
            else:
                # Fetch JavaScript from the web if not in the database
                _, extra_info = fetch_html([url], {'extract_js': True})
                results[url]['js'] = extra_info.get(url, {}).get('js', [])

    return results


def handle_client_connection(client_socket):
    request_data = client_socket.recv(4096)
    print("Received request data")
    request_dict = eval(request_data.decode())
    url = request_dict['url']
    settings = request_dict['settings']
    results = scrape([url], settings)
    print("Sending results")
    client_socket.sendall(str(results).encode())
    print("Results sent")
    client_socket.close()


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 5002))
    server_socket.listen(5)
    print("Server says: Listening on 0.0.0.0:5002")

    while True:
        client_socket, _ = server_socket.accept()
        client_handler = threading.Thread(target=handle_client_connection, args=(client_socket,))
        client_handler.start()


if __name__ == '__main__':
    threading.Thread(target=start_server).start()
    app.run(host='0.0.0.0', port=5006)