<?php

namespace App\Models;

use App\Enums\OrderStatus;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Serri\Alchemist\Concerns\HasAlchemyFormulas;
use Serri\Alchemist\Decorators\Relation;

class Order extends Model
{
    use HasFactory, HasAlchemyFormulas;

    public $timestamps = false;

    protected $guarded = ['id'];

    protected $fillable = [
        'order_number',
        'user_id',
        'shipping_address_id',
        'billing_address_id',
        'status',
        'subtotal',
        'discount',
        'tax',
        'total',
        'notes',
        'ordered_at',
        'confirmed_at',
        'shipped_at',
        'delivered_at',
        'cancelled_at',
    ];

    protected function casts(): array
    {
        return [
            'status' => OrderStatus::class,
            'subtotal' => 'decimal:2',
            'discount' => 'decimal:2',
            'tax' => 'decimal:2',
            'total' => 'decimal:2',
            'ordered_at' => 'datetime',
            'confirmed_at' => 'datetime',
            'shipped_at' => 'datetime',
            'delivered_at' => 'datetime',
            'cancelled_at' => 'datetime',
        ];
    }

    #[Relation]
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    #[Relation]
    public function items(): HasMany
    {
        return $this->hasMany(OrderItem::class);
    }

    #[Relation]
    public function shippingAddress(): BelongsTo
    {
        return $this->belongsTo(Address::class, 'shipping_address_id');
    }

    #[Relation]
    public function billingAddress(): BelongsTo
    {
        return $this->belongsTo(Address::class, 'billing_address_id');
    }

    public static function generateOrderNumber(): string
    {
        $prefix = 'ORD';
        $timestamp = now()->format('YmdHis');
        $random = strtoupper(substr(uniqid(), -4));

        return "{$prefix}-{$timestamp}-{$random}";
    }

    public function canBeCancelled(): bool
    {
        return in_array($this->status, [
            OrderStatus::Pending,
            OrderStatus::Confirmed,
        ]);
    }
}
