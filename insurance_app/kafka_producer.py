import json
import threading
from datetime import date
from datetime import datetime

from kafka import KafkaProducer as SyncKafkaProducer
from kafka.errors import KafkaError

from insurance_app.logger import logger


def json_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class KafkaProducer:
    def __init__(self, servers):
        try:
            self.producer = SyncKafkaProducer(
                bootstrap_servers=servers,
                value_serializer=lambda v: json.dumps(
                    v, default=json_serializer
                ).encode("utf-8"),
                retries=5,
                retry_backoff_ms=200,
                max_in_flight_requests_per_connection=5,
            )
        except KafkaError as error:
            logger.error(f"Failed to create Kafka producer: {error}", exc_info=True)
            raise
        self.messages = []
        self.batch_size = 10
        self.failed_messages = []

        self.messages_lock = threading.Lock()
        self.failed_messages_lock = threading.Lock()

    def send(self, topic, message):
        with self.messages_lock:
            self.messages.append((topic, message))
            if len(self.messages) >= self.batch_size:
                self.flush()

    def flush(self):
        with self.messages_lock:
            messages_to_send = self.messages.copy()
            self.messages = []

        try:
            for topic, message in messages_to_send:
                future = self.producer.send(topic, message)
                future.add_callback(self.on_send_success)
                future.add_errback(self.on_send_error, topic, message)
            self.producer.flush()
        except KafkaError as error:
            logger.error(f"Failed to flush messages to Kafka: {error}", exc_info=True)
            with self.failed_messages_lock:
                self.failed_messages.extend(messages_to_send)

    def on_send_success(self, record_metadata):
        logger.info(
            f"Message sent to {record_metadata.topic} partition {record_metadata.partition} "
            f"offset {record_metadata.offset}"
        )

    def on_send_error(self, excp, topic, message):
        logger.error(f"Failed to send message to {topic}: {excp}", exc_info=True)
        with self.failed_messages_lock:
            self.failed_messages.append((topic, message))

    def retry_failed_messages(self):
        with self.failed_messages_lock:
            if not self.failed_messages:
                return
            messages_to_retry = self.failed_messages.copy()
            self.failed_messages = []

        logger.info(f"Retrying {len(self.failed_messages)} failed messages")
        try:
            for topic, message in messages_to_retry:
                future = self.producer.send(topic, message)
                future.add_callback(self.on_send_success)
                future.add_errback(self.on_send_error, topic, message)
            self.producer.flush()
        except KafkaError as e:
            logger.error(f"Failed to resend messages to Kafka: {e}", exc_info=True)
            with self.failed_messages_lock:
                self.failed_messages.extend(messages_to_retry)

    def close(self):
        self.flush()
        self.retry_failed_messages()
        self.producer.close()
