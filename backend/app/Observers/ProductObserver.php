<?php

namespace App\Observers;

use App\Jobs\PublishKafkaEventJob;
use App\Models\Product;

class ProductObserver
{
    /**
     * Handle the Product "created" event.
     */
    public function created(Product $product): void
    {
        $this->dispatchProductEvent($product, 'product.created');
    }

    /**
     * Handle the Product "updated" event.
     */
    public function updated(Product $product): void
    {
        // Only dispatch if embedding-relevant fields changed
        if ($this->hasEmbeddingRelevantChanges($product)) {
            $this->dispatchProductEvent($product, 'product.updated');
        }
    }

    /**
     * Handle the Product "deleted" event.
     */
    public function deleted(Product $product): void
    {
        PublishKafkaEventJob::dispatch('product.deleted', [
            'event_type' => 'product.deleted',
            'product_id' => $product->id,
            'timestamp' => now()->toIso8601String(),
        ]);
    }

    /**
     * Check if any fields that affect the embedding have changed.
     */
    protected function hasEmbeddingRelevantChanges(Product $product): bool
    {
        return $product->isDirty(['name', 'description', 'category_id', 'price']);
    }

    /**
     * Dispatch a product event to Kafka.
     */
    protected function dispatchProductEvent(Product $product, string $eventType): void
    {
        // Eager load category if not loaded
        $product->loadMissing('category');

        PublishKafkaEventJob::dispatch($eventType, [
            'event_type' => $eventType,
            'product_id' => $product->id,
            'name' => $product->name,
            'description' => $product->description ?? '',
            'category_id' => $product->category_id,
            'category_name' => $product->category?->name ?? '',
            'price' => (float) $product->price,
            'timestamp' => now()->toIso8601String(),
        ]);
    }
}
