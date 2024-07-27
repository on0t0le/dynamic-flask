import os
import pika
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

def callback(ch, method, properties, body):
    modes = body.decode().split(',')
    for mode in modes:
        mode = mode.strip()
        if mode == "connector 1" and 3001 not in running_servers:
            p = Process(target=start_flask_server, args=(3001,))
            p.start()
            running_servers[3001] = p
        elif mode == "connector 2" and 3002 not in running_servers:
            p = Process(target=start_flask_server, args=(3002,))
            p.start()
            running_servers[3002] = p

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