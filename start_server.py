#!/usr/bin/env python3
"""
Lightweight local HTTP server for L'Impressionnisme Vivant.
Running the web app over HTTP provides a valid web origin,
resolving YouTube's embed restrictions (Error 153) that occur when
viewing via the file:// protocol.
"""
import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8080
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def run():
    Handler = http.server.SimpleHTTPRequestHandler
    try:
        with ReusableTCPServer(("", PORT), Handler) as httpd:
            url = f"http://localhost:{PORT}"
            print("=" * 65)
            print("🎨 L'Impressionnisme Vivant — Art Lovers' Local Web Guide")
            print(f" Serving live at: {url}")
            print(" HTTP origin active: YouTube embed player (Error 153) resolved.")
            print(" Press Ctrl+C to stop.")
            print("=" * 65)
            webbrowser.open(url)
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 98: # Address already in use
            alt_port = 8081
            print(f"Port {PORT} in use, trying port {alt_port}...")
            with ReusableTCPServer(("", alt_port), Handler) as httpd:
                url = f"http://localhost:{alt_port}"
                print(f"Serving at: {url}")
                webbrowser.open(url)
                httpd.serve_forever()
        else:
            raise e
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == '__main__':
    run()
