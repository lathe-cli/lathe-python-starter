import os

from src.app import create_server

port = int(os.environ.get("PORT", "3000"))
if not 1 <= port <= 65535:
    raise ValueError("PORT must be an integer between 1 and 65535")

server = create_server(port=port)
print(f"API listening on http://127.0.0.1:{port}")
server.serve_forever()

