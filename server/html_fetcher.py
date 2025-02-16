import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from DB_manager import *


def scrape(urls, settings):
    results = {}
    for url in urls:
        # Initialize the result dictionary for the current URL
        results[url] = {}

        # Fetch data from the database
        response = fetch_data_from_db(url)
        html_content = response.get('html_content')
        css_content = response.get('css', [])
        js_content = response.get('js', [])

        # Check if HTML is requested and available in the database
        if settings.get('extract_html', False):
            if html_content:
                results[url]['html'] = html_content
            else:
                # Fetch HTML from the web if not in the database
                html_contents, _ = fetch_html([url], {'extract_html': True})
                results[url]['html'] = html_contents.get(url)

        # Check if CSS is requested and available in the database
        if settings.get('extract_css', False):
            if css_content:
                results[url]['css'] = css_content
            else:
                # Fetch CSS from the web if not in the database
                _, extra_info = fetch_html([url], {'extract_css': True})
                results[url]['css'] = extra_info.get(url, {}).get('css', [])

        # Check if JavaScript is requested and available in the database
        if settings.get('extract_js', False):
            if js_content:
                results[url]['js'] = js_content
            else:
                # Fetch JavaScript from the web if not in the database
                _, extra_info = fetch_html([url], {'extract_js': True})
                results[url]['js'] = extra_info.get(url, {}).get('js', [])

    return results


def fetch_html(urls, settings):
    html_contents = {}
    extra_info = {}

    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Check if the request was successful
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract HTML
            html_content = soup.prettify()
            html_contents[url] = html_content if settings.get('extract_html', False) else None

            # Extract CSS
            css_content = []
            if settings.get('extract_css', False):
                # Inline CSS
                for style in soup.find_all('style'):
                    if style.string:
                        css_content.append(style.string)

                # External CSS
                for link in soup.find_all('link', rel='stylesheet'):
                    css_url = link.get('href')
                    if css_url:
                        # Handle relative URLs
                        if not css_url.startswith(('http://', 'https://')):
                            css_url = urljoin(url, css_url)
                        try:
                            css_response = requests.get(css_url)
                            css_response.raise_for_status()
                            css_content.append(css_response.text)
                        except requests.exceptions.RequestException as e:
                            print(f"Error fetching CSS {css_url}: {e}")

            # Extract JavaScript
            js_content = []
            if settings.get('extract_js', False):
                # Inline JS
                for script in soup.find_all('script'):
                    if script.string:  # Check if the script tag contains JavaScript code
                        js_content.append(script.string)

                    # External JS
                    elif script.get('src'):
                        js_url = script.get('src')
                        if not js_url.startswith(('http://', 'https://')):
                            # Handle relative URLs
                            js_url = urljoin(url, js_url)
                        try:
                            js_response = requests.get(js_url)
                            js_response.raise_for_status()
                            js_content.append(js_response.text)
                        except requests.exceptions.RequestException as e:
                            print(f"Error fetching JavaScript {js_url}: {e}")

            # Store all extracted data
            extra_info[url] = {
                'css': css_content,
                'js': js_content,
            }

            # Send data to the database manager
            request_dict = {
                'url': url,
                'html_content': html_content,
                'css': css_content,
                'js': js_content
            }
            store_data(request_dict)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            html_contents[url] = None

    return html_contents, extra_info
