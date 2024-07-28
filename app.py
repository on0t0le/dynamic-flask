import os
import pika
import json
from flask import Flask
from multiprocessing import Process

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

def callback(ch, method, properties, body):
    try:
        message = json.loads(body.decode())
        for connector, status in message.items():
            port = None
            if connector == "connector-1":
                port = 3001
            elif connector == "connector-2":
                port = 3002

            if port is not None:
                if status == "enabled" and port not in running_servers:
                    p = Process(target=start_flask_server, args=(port,))
                    p.start()
                    running_servers[port] = p
                    print(f"Enabled {connector} on port {port}")
                elif status == "disabled" and port in running_servers:
                    stop_flask_server(port)
                    print(f"Disabled {connector} on port {port}")
    except json.JSONDecodeError:
        print("Received message is not a valid JSON")

def listen_to_rabbitmq():
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
    rabbitmq_queue = os.getenv('RABBITMQ_QUEUE', 'mode_queue')
    rabbitmq_user = os.getenv('RABBITMQ_USER', 'guest')
    rabbitmq_password = os.getenv('RABBITMQ_PASSWORD', 'guest')

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=rabbitmq_host,
            port=rabbitmq_port,
            credentials=credentials
        )
    )
    channel = connection.channel()

    channel.queue_declare(queue=rabbitmq_queue)

    channel.basic_consume(
        queue=rabbitmq_queue,
        on_message_callback=callback,
        auto_ack=True
    )

    print('Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == "__main__":
    listen_to_rabbitmq()