<?php

namespace App\Jobs;

use App\Services\MLServiceClient;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;

class RecordRecommendationFeedbackJob implements ShouldQueue
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
        public int $userId,
        public int $productId,
        public string $action
    ) {}

    /**
     * Execute the job.
     */
    public function handle(MLServiceClient $mlClient): void
    {
        $mlClient->recordRecommendationFeedback(
            $this->userId,
            $this->productId,
            $this->action
        );

        Cache::forget("ml.recommendations.{$this->userId}.10");
    }

    /**
     * Handle a job failure.
     */
    public function failed(?\Throwable $exception): void
    {
        Log::error('Recommendation feedback job failed', [
            'user_id' => $this->userId,
            'product_id' => $this->productId,
            'action' => $this->action,
            'error' => $exception?->getMessage(),
        ]);
    }
}
