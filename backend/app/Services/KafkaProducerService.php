<?php

namespace App\Services;

use Illuminate\Support\Facades\Log;

class KafkaProducerService
{
    protected bool $enabled;

    protected string $brokers;

    protected int $timeout;

    protected int $retryTimes;

    protected int $retrySleep;

    /** @var array<string, string> */
    protected array $topics;

    /** @var \longlang\phpkafka\Producer\Producer|null */
    protected $producer = null;

    public function __construct()
    {
        $this->enabled = config('kafka.enabled', true);
        $this->brokers = config('kafka.brokers', 'localhost:29092');
        $this->timeout = config('kafka.timeout', 10);
        $this->retryTimes = config('kafka.retry_times', 3);
        $this->retrySleep = config('kafka.retry_sleep', 100);
        $this->topics = config('kafka.topics', []);
    }

    /**
     * Check if Kafka publishing is enabled.
     */
    public function isEnabled(): bool
    {
        return $this->enabled;
    }

    /**
     * Publish a message to a Kafka topic.
     *
     * @param  array<string, mixed>  $payload
     */
    public function publish(string $topic, array $payload): bool
    {
        if (! $this->enabled) {
            Log::debug('Kafka publishing disabled, skipping event', [
                'topic' => $topic,
                'event_type' => $payload['event_type'] ?? 'unknown',
            ]);

            return true;
        }

        $attempt = 0;
        $lastException = null;

        while ($attempt < $this->retryTimes) {
            try {
                $producer = $this->getProducer();
                $message = json_encode($payload, JSON_THROW_ON_ERROR);

                $producer->send($topic, $message);

                Log::info('Kafka event published', [
                    'topic' => $topic,
                    'event_type' => $payload['event_type'] ?? 'unknown',
                ]);

                return true;
            } catch (\Exception $e) {
                $lastException = $e;
                $attempt++;

                Log::warning('Kafka publish attempt failed', [
                    'topic' => $topic,
                    'attempt' => $attempt,
                    'error' => $e->getMessage(),
                ]);

                if ($attempt < $this->retryTimes) {
                    usleep($this->retrySleep * 1000);
                    $this->resetProducer();
                }
            }
        }

        Log::error('Kafka publish failed after all retries', [
            'topic' => $topic,
            'event_type' => $payload['event_type'] ?? 'unknown',
            'error' => $lastException?->getMessage(),
        ]);

        return false;
    }

    /**
     * Publish an order.completed event.
     *
     * @param  array<array{product_id: int, quantity: int, price: float}>  $items
     */
    public function publishOrderCompleted(
        int $orderId,
        string $orderNumber,
        int $userId,
        array $items,
        float $total
    ): bool {
        $topic = $this->topics['order_completed'] ?? 'order.completed';

        return $this->publish($topic, [
            'event_type' => 'order.completed',
            'order_id' => $orderId,
            'order_number' => $orderNumber,
            'user_id' => $userId,
            'items' => $items,
            'total' => $total,
            'timestamp' => now()->toIso8601String(),
        ]);
    }

    /**
     * Publish a review.created event.
     */
    public function publishReviewCreated(
        int $reviewId,
        int $userId,
        int $productId,
        int $rating,
        ?string $comment
    ): bool {
        $topic = $this->topics['review_created'] ?? 'review.created';

        return $this->publish($topic, [
            'event_type' => 'review.created',
            'review_id' => $reviewId,
            'user_id' => $userId,
            'product_id' => $productId,
            'rating' => $rating,
            'comment' => $comment,
            'timestamp' => now()->toIso8601String(),
        ]);
    }

    /**
     * Publish a user.interaction event.
     *
     * @param  array<string, mixed>  $metadata
     */
    public function publishUserInteraction(
        int $userId,
        int $productId,
        string $action,
        array $metadata = []
    ): bool {
        $topic = $this->topics['user_interaction'] ?? 'user.interaction';

        return $this->publish($topic, [
            'event_type' => 'user.interaction',
            'user_id' => $userId,
            'product_id' => $productId,
            'action' => $action,
            'metadata' => $metadata,
            'timestamp' => now()->toIso8601String(),
        ]);
    }

    /**
     * Publish a cart.updated event.
     *
     * @param  array<array{product_id: int, quantity: int}>  $items
     */
    public function publishCartUpdated(
        int $userId,
        string $action,
        ?int $affectedProductId,
        array $items
    ): bool {
        $topic = $this->topics['cart_updated'] ?? 'cart.updated';

        return $this->publish($topic, [
            'event_type' => 'cart.updated',
            'user_id' => $userId,
            'action' => $action,
            'affected_product_id' => $affectedProductId,
            'items' => $items,
            'timestamp' => now()->toIso8601String(),
        ]);
    }

    /**
     * Get or create the Kafka producer instance (lazy initialization).
     * Kafka classes are only loaded when this method is called.
     *
     * @return \longlang\phpkafka\Producer\Producer
     */
    protected function getProducer()
    {
        if ($this->producer === null) {
            // Only load Kafka classes when actually needed
            $configClass = \longlang\phpkafka\Producer\ProducerConfig::class;
            $producerClass = \longlang\phpkafka\Producer\Producer::class;

            $config = new $configClass;
            $config->setBootstrapServers($this->brokers);
            $config->setConnectTimeout($this->timeout);
            $config->setSendTimeout($this->timeout);
            $config->setRecvTimeout($this->timeout);
            $config->setAcks(-1);

            $this->producer = new $producerClass($config);
        }

        return $this->producer;
    }

    /**
     * Reset the producer connection (used during retries).
     */
    protected function resetProducer(): void
    {
        if ($this->producer !== null) {
            try {
                $this->producer->close();
            } catch (\Exception $e) {
                // Ignore close errors
            }
            $this->producer = null;
        }
    }

    /**
     * Clean up resources when the service is destroyed.
     */
    public function __destruct()
    {
        $this->resetProducer();
    }
}
