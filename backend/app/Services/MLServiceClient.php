<?php

namespace App\Services;

use Illuminate\Http\Client\ConnectionException;
use Illuminate\Http\Client\RequestException;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class MLServiceClient
{
    protected string $baseUrl;

    protected string $authToken;

    protected int $timeout;

    protected int $connectTimeout;

    protected int $retryTimes;

    protected int $retrySleep;

    public function __construct()
    {
        $this->baseUrl = config('services.ml.url');
        $this->authToken = config('services.ml.token');
        $this->timeout = config('services.ml.timeout', 5);
        $this->connectTimeout = config('services.ml.connect_timeout', 2);
        $this->retryTimes = config('services.ml.retry_times', 2);
        $this->retrySleep = config('services.ml.retry_sleep', 100);
    }

    /**
     * Check if the ML service is healthy and ready.
     */
    public function isHealthy(): bool
    {
        try {
            $response = Http::timeout(5)->get("{$this->baseUrl}/health/ready");

            return $response->successful() && ($response->json('status') === 'healthy' || $response->ok());
        } catch (\Exception $e) {
            Log::warning('ML Service health check failed', ['error' => $e->getMessage()]);

            return false;
        }
    }

    /**
     * Analyze sentiment of a text.
     *
     * @return array{score: float, label: string, confidence: float}|null
     */
    public function analyzeSentiment(string $text, int $userId): ?array
    {
        try {
            $response = $this->post('/api/v1/sentiment/analyze', [
                'text' => $text,
                'user_id' => $userId,
            ]);

            return $response;
        } catch (\Exception $e) {
            Log::error('Sentiment analysis failed', [
                'user_id' => $userId,
                'error' => $e->getMessage(),
            ]);

            return null;
        }
    }

    /**
     * Batch analyze sentiment for multiple texts.
     *
     * @param  array<array{text: string, user_id: int}>  $items
     * @return array|null
     */
    public function analyzeSentimentBatch(array $items): ?array
    {
        try {
            return $this->post('/api/v1/sentiment/batch', ['items' => $items]);
        } catch (\Exception $e) {
            Log::error('Batch sentiment analysis failed', ['error' => $e->getMessage()]);

            return null;
        }
    }

    /**
     * Get sentiment history for a user.
     */
    public function getSentimentHistory(int $userId): ?array
    {
        try {
            return $this->get("/api/v1/sentiment/history/{$userId}");
        } catch (\Exception $e) {
            Log::error('Failed to get sentiment history', [
                'user_id' => $userId,
                'error' => $e->getMessage(),
            ]);

            return null;
        }
    }

    /**
     * Get personalized recommendations for a user.
     *
     * @return array|null
     */
    public function getRecommendations(int $userId, int $limit = 10): ?array
    {
        $cacheKey = "ml.recommendations.{$userId}.{$limit}";

        return Cache::remember($cacheKey, 300, function () use ($userId, $limit) {
            try {
                return $this->get("/api/v1/recommendations/{$userId}", [
                    'limit' => $limit,
                ]);
            } catch (\Exception $e) {
                Log::error('Failed to get recommendations', [
                    'user_id' => $userId,
                    'error' => $e->getMessage(),
                ]);

                return null;
            }
        });
    }

    /**
     * Get similar products for a given product.
     *
     * @return array|null
     */
    public function getSimilarProducts(int $productId, int $limit = 5): ?array
    {
        $cacheKey = "ml.similar.{$productId}.{$limit}";

        return Cache::remember($cacheKey, 300, function () use ($productId, $limit) {
            try {
                return $this->get("/api/v1/recommendations/similar/{$productId}", [
                    'limit' => $limit,
                ]);
            } catch (\Exception $e) {
                Log::error('Failed to get similar products', [
                    'product_id' => $productId,
                    'error' => $e->getMessage(),
                ]);

                return null;
            }
        });
    }

    /**
     * Get frequently bought together products.
     *
     * @return array|null
     */
    public function getFrequentlyBoughtTogether(int $productId, int $limit = 5): ?array
    {
        $cacheKey = "ml.bought_together.{$productId}.{$limit}";

        return Cache::remember($cacheKey, 300, function () use ($productId, $limit) {
            try {
                return $this->get("/api/v1/recommendations/bought-together/{$productId}", [
                    'limit' => $limit,
                ]);
            } catch (\Exception $e) {
                Log::error('Failed to get frequently bought together', [
                    'product_id' => $productId,
                    'error' => $e->getMessage(),
                ]);

                return null;
            }
        });
    }

    /**
     * Record recommendation feedback.
     */
    public function recordRecommendationFeedback(int $userId, int $productId, string $action): bool
    {
        try {
            $this->post('/api/v1/recommendations/feedback', [
                'user_id' => $userId,
                'product_id' => $productId,
                'action' => $action,
            ]);

            // Invalidate recommendations cache for this user
            Cache::forget("ml.recommendations.{$userId}.10");

            return true;
        } catch (\Exception $e) {
            Log::error('Failed to record recommendation feedback', [
                'user_id' => $userId,
                'product_id' => $productId,
                'error' => $e->getMessage(),
            ]);

            return false;
        }
    }

    /**
     * Get user personality profile.
     *
     * @return array|null
     */
    public function getUserPersonality(int $userId): ?array
    {
        $cacheKey = "ml.personality.{$userId}";

        return Cache::remember($cacheKey, 600, function () use ($userId) {
            try {
                return $this->get("/api/v1/personality/profile/{$userId}");
            } catch (\Exception $e) {
                Log::error('Failed to get user personality', [
                    'user_id' => $userId,
                    'error' => $e->getMessage(),
                ]);

                return null;
            }
        });
    }

    /**
     * Get detailed personality traits for a user.
     *
     * @return array|null
     */
    public function getUserPersonalityTraits(int $userId): ?array
    {
        try {
            return $this->get("/api/v1/personality/traits/{$userId}");
        } catch (\Exception $e) {
            Log::error('Failed to get personality traits', [
                'user_id' => $userId,
                'error' => $e->getMessage(),
            ]);

            return null;
        }
    }

    /**
     * Update user personality based on an interaction.
     */
    public function updateUserPersonality(int $userId, string $interactionType, array $data = []): bool
    {
        try {
            $this->post('/api/v1/personality/update', array_merge([
                'user_id' => $userId,
                'interaction_type' => $interactionType,
            ], $data));

            // Invalidate personality cache
            Cache::forget("ml.personality.{$userId}");

            return true;
        } catch (\Exception $e) {
            Log::error('Failed to update user personality', [
                'user_id' => $userId,
                'error' => $e->getMessage(),
            ]);

            return false;
        }
    }

    /**
     * Make a GET request to the ML service.
     *
     * @throws RequestException|ConnectionException
     */
    protected function get(string $endpoint, array $query = []): array
    {
        $response = Http::withHeaders([
            'X-Service-Auth' => $this->authToken,
            'Accept' => 'application/json',
        ])
            ->connectTimeout($this->connectTimeout)
            ->timeout($this->timeout)
            ->retry($this->retryTimes, $this->retrySleep, function ($exception) {
                return $exception instanceof ConnectionException;
            })
            ->get("{$this->baseUrl}{$endpoint}", $query);

        $response->throw();

        return $response->json() ?? [];
    }

    /**
     * Make a POST request to the ML service.
     *
     * @throws RequestException|ConnectionException
     */
    protected function post(string $endpoint, array $data): array
    {
        $response = Http::withHeaders([
            'X-Service-Auth' => $this->authToken,
            'Accept' => 'application/json',
        ])
            ->connectTimeout($this->connectTimeout)
            ->timeout($this->timeout)
            ->retry($this->retryTimes, $this->retrySleep, function ($exception) {
                return $exception instanceof ConnectionException;
            })
            ->post("{$this->baseUrl}{$endpoint}", $data);

        $response->throw();

        return $response->json() ?? [];
    }
}
