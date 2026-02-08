<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('reviews', function (Blueprint $table) {
            $table->decimal('sentiment_score', 5, 4)->nullable()->after('comment');
            $table->string('sentiment_label', 20)->nullable()->after('sentiment_score');
            $table->decimal('sentiment_confidence', 5, 4)->nullable()->after('sentiment_label');
            $table->timestamp('sentiment_analyzed_at')->nullable()->after('sentiment_confidence');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('reviews', function (Blueprint $table) {
            $table->dropColumn([
                'sentiment_score',
                'sentiment_label',
                'sentiment_confidence',
                'sentiment_analyzed_at',
            ]);
        });
    }
};
