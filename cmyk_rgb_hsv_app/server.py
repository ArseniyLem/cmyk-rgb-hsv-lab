from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8000

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=Path(__file__).parent, **kwargs)

if __name__ == "__main__":
    print(f"Приложение запущено: http://{HOST}:{PORT}")
    print("Для остановки нажмите Ctrl+C")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
