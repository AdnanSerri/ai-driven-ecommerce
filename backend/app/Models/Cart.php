<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Serri\Alchemist\Concerns\HasAlchemyFormulas;
use Serri\Alchemist\Decorators\Relation;

class Cart extends Model
{
    use HasFactory, HasAlchemyFormulas;

    protected $guarded = ['id'];

    protected $fillable = [
        'user_id',
        'created_at',
        'updated_at',
    ];

    #[Relation]
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    #[Relation]
    public function items(): HasMany
    {
        return $this->hasMany(CartItem::class);
    }

    public function getTotalAttribute(): float
    {
        return $this->items->sum(function ($item) {
            return $item->product->price * $item->quantity;
        });
    }

    public function getItemCountAttribute(): int
    {
        return $this->items->sum('quantity');
    }
}
