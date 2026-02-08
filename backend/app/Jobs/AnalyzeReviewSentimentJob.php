<?php

namespace App\Jobs;

use App\Models\Review;
use App\Services\MLServiceClient;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Support\Facades\Log;

class AnalyzeReviewSentimentJob implements ShouldQueue
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
     */
    public function __construct(
        public int $reviewId
    ) {}

    /**
     * Execute the job.
     */
    public function handle(MLServiceClient $mlClient): void
    {
        $review = Review::find($this->reviewId);

        if (! $review || empty($review->comment)) {
            return;
        }

        $result = $mlClient->analyzeSentiment(
            $review->comment,
            $review->user_id
        );

        if ($result && isset($result['result'])) {
            $sentiment = $result['result'];

            $review->updateQuietly([
                'sentiment_score' => $sentiment['score'] ?? null,
                'sentiment_label' => $sentiment['label'] ?? null,
                'sentiment_confidence' => $sentiment['confidence'] ?? null,
                'sentiment_analyzed_at' => now(),
            ]);

            Log::info('Sentiment analysis completed', [
                'review_id' => $review->id,
                'sentiment_label' => $sentiment['label'] ?? 'unknown',
            ]);
        }
    }

    /**
     * Handle a job failure.
     */
    public function failed(?\Throwable $exception): void
    {
        Log::error('Sentiment analysis job failed', [
            'review_id' => $this->reviewId,
            'error' => $exception?->getMessage(),
        ]);
    }
}
