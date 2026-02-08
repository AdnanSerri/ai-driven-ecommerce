<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\TrackInteractionRequest;
use App\Jobs\PublishKafkaEventJob;
use Illuminate\Http\JsonResponse;

class InteractionController extends Controller
{
    public function track(TrackInteractionRequest $request): JsonResponse
    {
        $userId = $request->user()->id;

        PublishKafkaEventJob::dispatch('user.interaction', [
            'event_type' => 'user.interaction',
            'user_id' => $userId,
            'product_id' => $request->product_id,
            'action' => $request->action,
            'metadata' => $request->metadata ?? [],
            'timestamp' => now()->toIso8601String(),
        ]);

        return response()->json([
            'message' => 'Interaction tracked',
        ]);
    }
}
