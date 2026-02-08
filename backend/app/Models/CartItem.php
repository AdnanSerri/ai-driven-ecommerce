<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Serri\Alchemist\Concerns\HasAlchemyFormulas;
use Serri\Alchemist\Decorators\Relation;

class CartItem extends Model
{
    use HasFactory, HasAlchemyFormulas;

    public $timestamps = false;

    protected $guarded = ['id'];

    protected $fillable = [
        'cart_id',
        'product_id',
        'quantity',
        'added_at',
    ];

    protected function casts(): array
    {
        return [
            'quantity' => 'integer',
            'added_at' => 'datetime',
        ];
    }

    #[Relation]
    public function cart(): BelongsTo
    {
        return $this->belongsTo(Cart::class);
    }

    #[Relation]
    public function product(): BelongsTo
    {
        return $this->belongsTo(Product::class);
    }

    public function getSubtotalAttribute(): float
    {
        return $this->product->price * $this->quantity;
    }
}
