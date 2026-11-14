import os
import pika
import json
import uuid
import logging

logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")


def get_connection():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300
    )
    return pika.BlockingConnection(parameters)


def send_rpc_request(task_data: dict, timeout_seconds: int = 30):
    connection = get_connection()
    channel = connection.channel()

    channel.queue_declare(queue='ai_tasks', durable=True)
    result = channel.queue_declare(queue='', exclusive=True)
    callback_queue = result.method.queue

    corr_id = str(uuid.uuid4())
    task_data["correlation_id"] = corr_id

    channel.basic_publish(
        exchange='',
        routing_key='ai_tasks',
        properties=pika.BasicProperties(
            reply_to=callback_queue,
            correlation_id=corr_id,
        ),
        body=json.dumps(task_data)
    )

    response = None
    def on_response(ch, method, props, body):
        nonlocal response
        if props.correlation_id == corr_id:
            response = json.loads(body)
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=callback_queue, on_message_callback=on_response, auto_ack=False)
    connection.process_data_events(time_limit=timeout_seconds)
    connection.close()

    if response is None:
        raise TimeoutError("AI-server not responding")
    return response