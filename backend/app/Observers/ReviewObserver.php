<?php

namespace App\Observers;

use App\Jobs\AnalyzeReviewSentimentJob;
use App\Jobs\PublishKafkaEventJob;
use App\Models\Review;

class ReviewObserver
{
    /**
     * Handle the Review "created" event.
     */
    public function created(Review $review): void
    {
        $this->dispatchSentimentAnalysis($review);
        $this->dispatchReviewCreatedEvent($review);
    }

    /**
     * Handle the Review "updated" event.
     */
    public function updated(Review $review): void
    {
        if ($review->isDirty('comment')) {
            $this->dispatchSentimentAnalysis($review);
        }
    }

    /**
     * Dispatch sentiment analysis as a queued job.
     */
    protected function dispatchSentimentAnalysis(Review $review): void
    {
        if (empty($review->comment)) {
            return;
        }

        AnalyzeReviewSentimentJob::dispatch($review->id);
    }

    /**
     * Dispatch the review.created Kafka event.
     */
    protected function dispatchReviewCreatedEvent(Review $review): void
    {
        PublishKafkaEventJob::dispatch('review.created', [
            'event_type' => 'review.created',
            'review_id' => $review->id,
            'user_id' => $review->user_id,
            'product_id' => $review->product_id,
            'rating' => $review->rating,
            'comment' => $review->comment,
            'timestamp' => now()->toIso8601String(),
        ]);
    }
}
