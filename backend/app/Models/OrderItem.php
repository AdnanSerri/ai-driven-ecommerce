<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Serri\Alchemist\Concerns\HasAlchemyFormulas;
use Serri\Alchemist\Decorators\Relation;

class OrderItem extends Model
{
    use HasFactory, HasAlchemyFormulas;

    public $timestamps = false;

    protected $guarded = ['id'];

    protected $fillable = [
        'order_id',
        'product_id',
        'product_name',
        'product_price',
        'quantity',
        'subtotal',
    ];

    protected function casts(): array
    {
        return [
            'product_price' => 'decimal:2',
            'quantity' => 'integer',
            'subtotal' => 'decimal:2',
        ];
    }

    #[Relation]
    public function order(): BelongsTo
    {
        return $this->belongsTo(Order::class);
    }

    #[Relation]
    public function product(): BelongsTo
    {
        return $this->belongsTo(Product::class);
    }
}
