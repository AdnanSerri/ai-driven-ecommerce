<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Serri\Alchemist\Concerns\HasAlchemyFormulas;
use Serri\Alchemist\Decorators\Relation;

class Review extends Model
{
    use HasFactory, HasAlchemyFormulas;

    public $timestamps = false;

    protected $guarded = ['id'];

    protected $fillable = [
        'user_id',
        'product_id',
        'rating',
        'comment',
        'sentiment_score',
        'sentiment_label',
        'sentiment_confidence',
        'sentiment_analyzed_at',
        'created_at',
    ];

    protected function casts(): array
    {
        return [
            'rating' => 'integer',
            'sentiment_score' => 'decimal:4',
            'sentiment_confidence' => 'decimal:4',
            'sentiment_analyzed_at' => 'datetime',
            'created_at' => 'datetime',
        ];
    }

    public function hasSentiment(): bool
    {
        return $this->sentiment_label !== null;
    }

    public function getSentimentColorAttribute(): string
    {
        return match ($this->sentiment_label) {
            'positive' => 'success',
            'negative' => 'danger',
            'neutral' => 'gray',
            default => 'gray',
        };
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