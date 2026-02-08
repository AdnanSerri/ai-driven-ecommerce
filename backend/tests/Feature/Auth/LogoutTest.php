<?php

use App\Models\User;
use Laravel\Sanctum\Sanctum;

it('logs out an authenticated user', function () {
    $user = User::factory()->create();
    Sanctum::actingAs($user);

    $response = $this->postJson('/api/logout');

    $response->assertSuccessful()
        ->assertJson(['message' => 'Logged out successfully']);
});

it('fails logout without authentication', function () {
    $response = $this->postJson('/api/logout');

    $response->assertUnauthorized();
});
