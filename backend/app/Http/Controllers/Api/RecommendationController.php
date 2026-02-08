<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Jobs\RecordRecommendationFeedbackJob;
use App\Models\Product;
use App\Services\MLServiceClient;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class RecommendationController extends Controller
{
    public function __construct(
        protected MLServiceClient $mlClient
    ) {}

    /**
     * Get personalized recommendations for the authenticated user.
     */
    public function index(Request $request): JsonResponse
    {
        $request->validate([
            'limit' => 'nullable|integer|min:1|max:50',
        ]);

        $userId = $request->user()->id;
        $limit = $request->input('limit', 10);

        $recommendations = $this->mlClient->getRecommendations($userId, $limit);

        if ($recommendations === null) {
            return response()->json([
                'message' => 'Unable to fetch recommendations at this time',
                'data' => [],
            ], 503);
        }

        // Fetch actual product data for the recommended product IDs
        $productIds = collect($recommendations['recommendations'] ?? [])->pluck('product_id');
        $products = Product::whereIn('id', $productIds)
            ->with(['category', 'images'])
            ->get()
            ->keyBy('id');

        $data = collect($recommendations['recommendations'] ?? [])->map(function ($rec) use ($products) {
            $product = $products->get($rec['product_id']);

            if (! $product) {
                return null;
            }

            return [
                'product' => [
                    'id' => $product->id,
                    'name' => $product->name,
                    'price' => $product->price,
                    'image_url' => $product->primary_image?->image_url ?? $product->image_url,
                    'category' => $product->category?->name,
                    'in_stock' => $product->isInStock(),
                ],
                'score' => $rec['score'] ?? null,
                'reason' => $rec['reason'] ?? null,
            ];
        })->filter()->values();

        return response()->json([
            'data' => $data,
            'meta' => [
                'user_id' => $userId,
                'personality_type' => $recommendations['personality_type'] ?? null,
            ],
        ]);
    }

    /**
     * Get similar products for a given product.
     */
    public function similar(Request $request, Product $product): JsonResponse
    {
        $request->validate([
            'limit' => 'nullable|integer|min:1|max:20',
        ]);

        $limit = $request->input('limit', 5);

        $similar = $this->mlClient->getSimilarProducts($product->id, $limit);

        if ($similar === null) {
            return response()->json([
                'message' => 'Unable to fetch similar products at this time',
                'data' => [],
            ], 503);
        }

        // Fetch actual product data
        $productIds = collect($similar['similar_products'] ?? [])->pluck('product_id');
        $products = Product::whereIn('id', $productIds)
            ->with(['category', 'images'])
            ->get()
            ->keyBy('id');

        $data = collect($similar['similar_products'] ?? [])->map(function ($rec) use ($products) {
            $product = $products->get($rec['product_id']);

            if (! $product) {
                return null;
            }

            return [
                'product' => [
                    'id' => $product->id,
                    'name' => $product->name,
                    'price' => $product->price,
                    'image_url' => $product->primary_image?->image_url ?? $product->image_url,
                    'category' => $product->category?->name,
                    'in_stock' => $product->isInStock(),
                ],
                'similarity_score' => $rec['similarity_score'] ?? null,
            ];
        })->filter()->values();

        return response()->json([
            'data' => $data,
            'meta' => [
                'source_product_id' => $product->id,
                'source_product_name' => $product->name,
            ],
        ]);
    }

    /**
     * Record feedback for a recommendation.
     */
    public function feedback(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'product_id' => 'required|integer|exists:products,id',
            'action' => 'required|string|in:clicked,purchased,dismissed,viewed',
        ]);

        $userId = $request->user()->id;

        RecordRecommendationFeedbackJob::dispatch(
            $userId,
            $validated['product_id'],
            $validated['action']
        );

        return response()->json([
            'message' => 'Feedback recorded successfully',
        ]);
    }
}
