<?php

namespace App\Http\Controllers\Api;

use App\Formulas\ReviewFormula;
use App\Http\Controllers\Controller;
use App\Http\Requests\StoreReviewRequest;
use App\Models\Product;
use App\Models\Review;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Serri\Alchemist\Facades\Alchemist;

class ReviewController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $reviews = $request->user()
            ->reviews()
            ->with('product')
            ->latest('created_at')
            ->paginate(15);

        Review::setFormula(ReviewFormula::WithProduct);

        return response()->json(
            Alchemist::brewBatch($reviews)
        );
    }

    public function productReviews(Product $product): JsonResponse
    {
        $reviews = $product->reviews()
            ->with('user')
            ->latest('created_at')
            ->paginate(15);

        Review::setFormula(ReviewFormula::WithUser);

        return response()->json(
            Alchemist::brewBatch($reviews)
        );
    }

    public function store(StoreReviewRequest $request): JsonResponse
    {
        $review = Review::create([
            'user_id' => $request->user()->id,
            'product_id' => $request->product_id,
            'rating' => $request->rating,
            'comment' => $request->comment,
            'created_at' => now(),
        ]);

        $review->load('product');

        Review::setFormula(ReviewFormula::WithProduct);

        return response()->json([
            'message' => 'Review submitted successfully',
            'data' => Alchemist::brew($review),
        ], 201);
    }
}
