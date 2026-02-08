<?php

namespace App\Jobs;

use App\Services\KafkaProducerService;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Support\Facades\Log;

class PublishKafkaEventJob implements ShouldQueue
{
    use Queueable;

    /**
     * The number of times the job may be attempted.
     */
    public int $tries = 3;

    /**
     * The number of seconds to wait before retrying the job.
     */
    public int $backoff = 5;

    /**
     * Create a new job instance.
     *
     * @param  array<string, mixed>  $payload
     */
    public function __construct(
        public string $eventType,
        public array $payload
    ) {}

    /**
     * Execute the job.
     */
    public function handle(KafkaProducerService $kafkaService): void
    {
        $topic = $this->getTopicForEventType();

        if ($topic === null) {
            Log::error('Unknown Kafka event type', [
                'event_type' => $this->eventType,
            ]);

            return;
        }

        $success = $kafkaService->publish($topic, $this->payload);

        if (! $success) {
            throw new \RuntimeException("Failed to publish Kafka event: {$this->eventType}");
        }
    }

    /**
     * Get the Kafka topic for the event type.
     */
    protected function getTopicForEventType(): ?string
    {
        $topics = config('kafka.topics', []);

        return match ($this->eventType) {
            'order.completed' => $topics['order_completed'] ?? 'order.completed',
            'review.created' => $topics['review_created'] ?? 'review.created',
            'user.interaction' => $topics['user_interaction'] ?? 'user.interaction',
            'cart.updated' => $topics['cart_updated'] ?? 'cart.updated',
            'product.created' => $topics['product_created'] ?? 'product.created',
            'product.updated' => $topics['product_updated'] ?? 'product.updated',
            'product.deleted' => $topics['product_deleted'] ?? 'product.deleted',
            default => null,
        };
    }

    /**
     * Handle a job failure.
     */
    public function failed(?\Throwable $exception): void
    {
        Log::error('Kafka event job failed', [
            'event_type' => $this->eventType,
            'payload' => $this->payload,
            'error' => $exception?->getMessage(),
        ]);
    }
}
