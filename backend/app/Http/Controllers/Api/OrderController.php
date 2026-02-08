<?php

namespace App\Http\Controllers\Api;

use App\Enums\OrderStatus;
use App\Formulas\OrderFormula;
use App\Formulas\OrderItemFormula;
use App\Http\Controllers\Controller;
use App\Models\Order;
use App\Models\OrderItem;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Serri\Alchemist\Facades\Alchemist;

class OrderController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $orders = $request->user()
            ->orders()
            ->latest('ordered_at')
            ->paginate(15);

        Order::setFormula(OrderFormula::List);

        return response()->json(
            Alchemist::brewBatch($orders)
        );
    }

    public function show(Request $request, Order $order): JsonResponse
    {
        if ($order->user_id !== $request->user()->id) {
            return response()->json([
                'message' => 'Order not found',
            ], 404);
        }

        $order->load(['items.product', 'shippingAddress', 'billingAddress']);

        Order::setFormula(OrderFormula::Detail);
        OrderItem::setFormula(OrderItemFormula::WithProduct);

        return response()->json([
            'data' => Alchemist::brew($order),
        ]);
    }

    public function cancel(Request $request, Order $order): JsonResponse
    {
        if ($order->user_id !== $request->user()->id) {
            return response()->json([
                'message' => 'Order not found',
            ], 404);
        }

        if (! $order->canBeCancelled()) {
            return response()->json([
                'message' => 'Order cannot be cancelled',
            ], 422);
        }

        foreach ($order->items as $item) {
            $item->product->incrementStock($item->quantity);
        }

        $order->update([
            'status' => OrderStatus::Cancelled,
            'cancelled_at' => now(),
        ]);

        Order::setFormula(OrderFormula::Detail);

        return response()->json([
            'message' => 'Order cancelled successfully',
            'data' => Alchemist::brew($order),
        ]);
    }
}
