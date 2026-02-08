<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Serri\Alchemist\Concerns\HasAlchemyFormulas;
use Serri\Alchemist\Decorators\Relation;

class Product extends Model
{
    use HasFactory, HasAlchemyFormulas;

    public $timestamps = false;

    protected $guarded = ['id'];

    protected $fillable = [
        'name',
        'description',
        'price',
        'stock',
        'low_stock_threshold',
        'track_stock',
        'category_id',
        'image_url',
        'created_at',
    ];

    protected function casts(): array
    {
        return [
            'price' => 'decimal:2',
            'stock' => 'integer',
            'low_stock_threshold' => 'integer',
            'track_stock' => 'boolean',
            'created_at' => 'datetime',
        ];
    }

    #[Relation]
    public function category(): BelongsTo
    {
        return $this->belongsTo(Category::class);
    }

    #[Relation]
    public function reviews(): HasMany
    {
        return $this->hasMany(Review::class);
    }

    #[Relation]
    public function images(): HasMany
    {
        return $this->hasMany(ProductImage::class)->orderBy('sort_order');
    }

    #[Relation]
    public function wishlists(): HasMany
    {
        return $this->hasMany(Wishlist::class);
    }

    #[Relation]
    public function orderItems(): HasMany
    {
        return $this->hasMany(OrderItem::class);
    }

    public function getPrimaryImageAttribute(): ?ProductImage
    {
        return $this->images->firstWhere('is_primary', true) ?? $this->images->first();
    }

    public function isInStock(): bool
    {
        if (! $this->track_stock) {
            return true;
        }

        return $this->stock > 0;
    }

    public function hasLowStock(): bool
    {
        if (! $this->track_stock) {
            return false;
        }

        return $this->stock <= $this->low_stock_threshold;
    }

    public function decrementStock(int $quantity): bool
    {
        if (! $this->track_stock) {
            return true;
        }

        if ($this->stock < $quantity) {
            return false;
        }

        $this->decrement('stock', $quantity);

        return true;
    }

    public function incrementStock(int $quantity): void
    {
        if ($this->track_stock) {
            $this->increment('stock', $quantity);
        }
    }
}