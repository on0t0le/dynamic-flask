import os
import mysql.connector
from flask import Flask
from multiprocessing import Process
import time

# Global dictionary to keep track of running servers
running_servers = {}

def start_flask_server(port):
    app = Flask(__name__)

    @app.route('/')
    def hello():
        return f'Hello from Flask server on port {port}'

    app.run(port=port)

def stop_flask_server(port):
    if port in running_servers:
        running_servers[port].terminate()
        running_servers[port].join()
        del running_servers[port]
        print(f"Flask server on port {port} stopped")

def fetch_modes_from_db():
    db_config = {
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'password'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'test')
    }
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT mode_name, mode_enabled FROM modes")
    modes = cursor.fetchall()
    cursor.close()
    conn.close()
    return modes

def update_servers():
    modes = fetch_modes_from_db()
    for mode in modes:
        connector, status = mode['mode_name'], mode['mode_enabled']
        port = None
        if connector == "connector-1":
            port = 3001
        elif connector == "connector-2":
            port = 3002

        if port is not None:
            if status == 1 and port not in running_servers:
                p = Process(target=start_flask_server, args=(port,))
                p.start()
                running_servers[port] = p
                print(f"Enabled {connector} on port {port}")
            elif status == 0 and port in running_servers:
                stop_flask_server(port)
                print(f"Disabled {connector} on port {port}")

def main_loop():
    while True:
        update_servers()
        time.sleep(10)  # Check for changes every 10 seconds

if __name__ == "__main__":
    main_loop()