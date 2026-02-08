<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Services\MLServiceClient;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class PersonalityController extends Controller
{
    public function __construct(
        protected MLServiceClient $mlClient
    ) {}

    /**
     * Get the authenticated user's personality profile.
     */
    public function profile(Request $request): JsonResponse
    {
        $userId = $request->user()->id;

        $profile = $this->mlClient->getUserPersonality($userId);

        if ($profile === null) {
            return response()->json([
                'message' => 'Unable to fetch personality profile at this time',
                'data' => null,
            ], 503);
        }

        $profileData = $profile['profile'] ?? [];

        return response()->json([
            'data' => [
                'user_id' => $userId,
                'personality_type' => $profileData['personality_type'] ?? null,
                'dimensions' => $profileData['dimensions'] ?? [],
                'confidence' => $profileData['confidence'] ?? null,
                'data_points' => $profileData['data_points'] ?? null,
                'last_updated' => $profileData['last_updated'] ?? null,
            ],
        ]);
    }

    /**
     * Get detailed personality traits for the authenticated user.
     */
    public function traits(Request $request): JsonResponse
    {
        $userId = $request->user()->id;

        $traits = $this->mlClient->getUserPersonalityTraits($userId);

        if ($traits === null) {
            return response()->json([
                'message' => 'Unable to fetch personality traits at this time',
                'data' => null,
            ], 503);
        }

        return response()->json([
            'data' => $traits,
        ]);
    }

    /**
     * Record a user interaction that updates their personality profile.
     */
    public function recordInteraction(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'interaction_type' => 'required|string|in:view,click,purchase,review,wishlist,cart_add,cart_remove',
            'product_id' => 'nullable|integer|exists:products,id',
            'category_id' => 'nullable|integer|exists:categories,id',
            'metadata' => 'nullable|array',
        ]);

        $userId = $request->user()->id;

        $success = $this->mlClient->updateUserPersonality(
            $userId,
            $validated['interaction_type'],
            array_filter([
                'product_id' => $validated['product_id'] ?? null,
                'category_id' => $validated['category_id'] ?? null,
                'metadata' => $validated['metadata'] ?? null,
            ])
        );

        if (! $success) {
            return response()->json([
                'message' => 'Unable to record interaction at this time',
            ], 503);
        }

        return response()->json([
            'message' => 'Interaction recorded successfully',
        ]);
    }
}
