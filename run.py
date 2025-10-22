#!/usr/bin/env python3
from wsgiref.simple_server import make_server
from app import application

if __name__ == "__main__":
    with make_server("127.0.0.1", 8000, application) as httpd:
        print("Serving on http://127.0.0.1:8000 …")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

