<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Serri\Alchemist\Concerns\HasAlchemyFormulas;
use Serri\Alchemist\Decorators\Relation;

class Category extends Model
{
    use HasFactory, HasAlchemyFormulas;

    protected $guarded = ['id', 'created_at', 'updated_at'];

    protected $fillable = [
        'name',
        'parent_id',
    ];

    #[Relation]
    public function parent(): BelongsTo
    {
        return $this->belongsTo(Category::class, 'parent_id');
    }

    #[Relation]
    public function children(): HasMany
    {
        return $this->hasMany(Category::class, 'parent_id');
    }

    #[Relation]
    public function products(): HasMany
    {
        return $this->hasMany(Product::class);
    }
}