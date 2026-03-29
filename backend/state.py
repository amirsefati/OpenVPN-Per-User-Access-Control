from fastapi import WebSocket


online_usernames: set[str] = set()
online_connections: set[WebSocket] = set()

