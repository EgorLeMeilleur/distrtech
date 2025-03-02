import os
import json
import webbrowser
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query_components = parse_qs(urlparse(self.path).query)
        if 'code' in query_components:
            self.server.callback_server.auth_code = query_components['code'][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Authorization successful. You can close this window.")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing code parameter.")

    def log_message(self, format, *args):
        return


class CallbackServer:
    def __init__(self):
        self.server = HTTPServer(('localhost', 8000), OAuthCallbackHandler)
        self.server.callback_server = self
        self.auth_code = None

    def start(self):
        thread = threading.Thread(target=self.server.serve_forever)
        thread.daemon = True
        thread.start()

    def wait_for_code(self):
        while self.auth_code is None:
            pass
        self.server.shutdown()
        return self.auth_code

    def get_redirect_uri(self):
        host, port = self.server.server_address
        return f"http://{host}:{port}/"


def get_github_access_token():
    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise Exception("Please set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET environment variables.")

    cb_server = CallbackServer()
    cb_server.start()
    redirect_uri = cb_server.get_redirect_uri()

    auth_url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        "&scope=repo"
    )
    print("Opening browser for authorization...")
    webbrowser.open(auth_url)

    code = cb_server.wait_for_code()
    print("Authorization code received:", code)

    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri
    }
    response = requests.post(token_url, headers=headers, data=data)
    token_json = response.json()
    if "access_token" not in token_json:
        raise Exception("Error obtaining access token: " + json.dumps(token_json))
    access_token = token_json["access_token"]
    print("Access token obtained.")
    return access_token