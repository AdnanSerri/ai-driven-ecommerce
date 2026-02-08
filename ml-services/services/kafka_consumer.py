"""
Kafka Consumer Service.
Consumes events from Laravel and triggers ML processing.
"""

import asyncio
import json
import structlog
from typing import Any, Callable, Optional

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError, KafkaError

from config import get_settings

logger = structlog.get_logger(__name__)


class KafkaConsumerService:
    """
    Async Kafka consumer for processing events from Laravel.
    Subscribes to multiple topics and routes messages to handlers.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._running = False
        self._connected = False
        self._task: Optional[asyncio.Task] = None
        self._handlers: dict[str, Callable] = {}

    def register_handler(self, topic: str, handler: Callable) -> None:
        """
        Register a handler for a specific topic.

        Args:
            topic: Kafka topic name
            handler: Async function to handle messages from this topic
        """
        self._handlers[topic] = handler
        logger.debug("Registered handler", topic=topic, handler=handler.__name__)

    async def start(self) -> None:
        """
        Start the Kafka consumer as a background task.
        """
        if self._running:
            logger.warning("Kafka consumer already running")
            return

        try:
            self._consumer = AIOKafkaConsumer(
                *self.settings.kafka_topic_list,
                bootstrap_servers=self.settings.kafka_bootstrap_servers,
                group_id=self.settings.kafka_consumer_group,
                auto_offset_reset=self.settings.kafka_auto_offset_reset,
                enable_auto_commit=self.settings.kafka_enable_auto_commit,
                session_timeout_ms=self.settings.kafka_session_timeout_ms,
                # Don't deserialize here - do it in _process_message for better error handling
            )

            await self._consumer.start()
            self._connected = True
            self._running = True

            logger.info(
                "Kafka consumer connected",
                topics=self.settings.kafka_topic_list,
                group_id=self.settings.kafka_consumer_group,
                bootstrap_servers=self.settings.kafka_bootstrap_servers,
            )

            # Start consuming in background
            self._task = asyncio.create_task(self._consume_loop())

        except KafkaConnectionError as e:
            logger.warning(
                "Kafka connection failed - consumer will not process events",
                error=str(e),
                bootstrap_servers=self.settings.kafka_bootstrap_servers,
            )
            self._connected = False
        except Exception as e:
            logger.error(
                "Kafka consumer startup failed",
                error=str(e),
            )
            self._connected = False

    async def stop(self) -> None:
        """
        Stop the Kafka consumer gracefully.
        """
        if not self._running:
            return

        logger.info("Stopping Kafka consumer...")
        self._running = False

        # Cancel the consume task
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        # Stop the consumer
        if self._consumer:
            try:
                await self._consumer.stop()
            except Exception as e:
                logger.warning("Error stopping Kafka consumer", error=str(e))

        self._connected = False
        logger.info("Kafka consumer stopped")

    async def _consume_loop(self) -> None:
        """
        Main consume loop - processes messages and routes to handlers.
        """
        logger.info("Kafka consume loop started")

        try:
            async for message in self._consumer:
                if not self._running:
                    break

                try:
                    await self._process_message(message)
                except Exception as e:
                    logger.error(
                        "Error processing Kafka message",
                        topic=message.topic,
                        partition=message.partition,
                        offset=message.offset,
                        error=str(e),
                    )
                    # Continue processing other messages

        except asyncio.CancelledError:
            logger.info("Kafka consume loop cancelled")
            raise
        except KafkaError as e:
            logger.error("Kafka error in consume loop", error=str(e))
            self._connected = False
        except Exception as e:
            logger.error("Unexpected error in consume loop", error=str(e))
            self._connected = False

    async def _process_message(self, message: Any) -> None:
        """
        Process a single Kafka message.

        Args:
            message: Kafka message object
        """
        topic = message.topic

        # Deserialize message value with error handling
        try:
            raw_value = message.value
            if isinstance(raw_value, bytes):
                value = json.loads(raw_value.decode("utf-8"))
            else:
                value = raw_value
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse Kafka message JSON",
                topic=topic,
                partition=message.partition,
                offset=message.offset,
                error=str(e),
                raw_value=message.value[:200] if message.value else None,
            )
            return  # Skip this message

        logger.debug(
            "Processing Kafka message",
            topic=topic,
            partition=message.partition,
            offset=message.offset,
        )

        # Find handler for this topic
        handler = self._handlers.get(topic)
        if handler:
            try:
                await handler(value)
                logger.info(
                    "Successfully processed event",
                    topic=topic,
                    event_type=value.get("event_type", "unknown"),
                )
            except Exception as e:
                logger.error(
                    "Handler error",
                    topic=topic,
                    handler=handler.__name__,
                    error=str(e),
                )
                # Don't re-raise - we want to continue processing other messages
        else:
            logger.warning(
                "No handler registered for topic",
                topic=topic,
            )

    @property
    def is_connected(self) -> bool:
        """Check if consumer is connected to Kafka."""
        return self._connected

    @property
    def is_running(self) -> bool:
        """Check if consumer is running."""
        return self._running

    async def health_check(self) -> bool:
        """
        Check if Kafka consumer is healthy.

        Returns:
            True if consumer is connected and running
        """
        return self._connected and self._running


# Global instance
_kafka_consumer: Optional[KafkaConsumerService] = None


def get_kafka_consumer() -> KafkaConsumerService:
    """Get the Kafka consumer instance."""
    global _kafka_consumer
    if _kafka_consumer is None:
        _kafka_consumer = KafkaConsumerService()
    return _kafka_consumer


async def start_kafka_consumer() -> KafkaConsumerService:
    """
    Start the Kafka consumer with all handlers registered.
    Called during application startup.
    """
    from services.event_handlers import (
        handle_user_interaction,
        handle_review_created,
        handle_order_completed,
        handle_cart_updated,
        handle_product_created,
        handle_product_updated,
        handle_product_deleted,
    )

    consumer = get_kafka_consumer()

    # Register handlers for each topic
    consumer.register_handler("user.interaction", handle_user_interaction)
    consumer.register_handler("review.created", handle_review_created)
    consumer.register_handler("order.completed", handle_order_completed)
    consumer.register_handler("cart.updated", handle_cart_updated)
    consumer.register_handler("product.created", handle_product_created)
    consumer.register_handler("product.updated", handle_product_updated)
    consumer.register_handler("product.deleted", handle_product_deleted)

    # Start consuming
    await consumer.start()

    return consumer


async def stop_kafka_consumer() -> None:
    """
    Stop the Kafka consumer.
    Called during application shutdown.
    """
    global _kafka_consumer
    if _kafka_consumer is not None:
        await _kafka_consumer.stop()
        _kafka_consumer = None
