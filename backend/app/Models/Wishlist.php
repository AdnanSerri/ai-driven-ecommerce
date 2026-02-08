<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Serri\Alchemist\Concerns\HasAlchemyFormulas;
use Serri\Alchemist\Decorators\Relation;

class Wishlist extends Model
{
    use HasFactory, HasAlchemyFormulas;

    public $timestamps = false;

    protected $guarded = ['id'];

    protected $fillable = [
        'user_id',
        'product_id',
        'added_at',
    ];

    protected function casts(): array
    {
        return [
            'added_at' => 'datetime',
        ];
    }

    #[Relation]
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    #[Relation]
    public function product(): BelongsTo
    {
        return $this->belongsTo(Product::class);
    }
}
