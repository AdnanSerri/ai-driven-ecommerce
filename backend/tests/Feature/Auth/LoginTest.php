<?php

use App\Models\User;

it('logs in a user with valid credentials', function () {
    $user = User::factory()->create([
        'email' => 'test@example.com',
        'password' => bcrypt('password123'),
    ]);

    $response = $this->postJson('/api/login', [
        'email' => 'test@example.com',
        'password' => 'password123',
    ]);

    $response->assertSuccessful()
        ->assertJsonStructure([
            'message',
            'user' => ['id', 'name', 'email'],
            'token',
        ]);
});

it('fails login with invalid email', function () {
    User::factory()->create([
        'email' => 'test@example.com',
        'password' => bcrypt('password123'),
    ]);

    $response = $this->postJson('/api/login', [
        'email' => 'wrong@example.com',
        'password' => 'password123',
    ]);

    $response->assertUnauthorized()
        ->assertJson(['message' => 'Invalid credentials']);
});

it('fails login with invalid password', function () {
    User::factory()->create([
        'email' => 'test@example.com',
        'password' => bcrypt('password123'),
    ]);

    $response = $this->postJson('/api/login', [
        'email' => 'test@example.com',
        'password' => 'wrongpassword',
    ]);

    $response->assertUnauthorized()
        ->assertJson(['message' => 'Invalid credentials']);
});

it('fails login with missing email', function () {
    $response = $this->postJson('/api/login', [
        'password' => 'password123',
    ]);

    $response->assertUnprocessable()
        ->assertJsonValidationErrors(['email']);
});

it('fails login with missing password', function () {
    $response = $this->postJson('/api/login', [
        'email' => 'test@example.com',
    ]);

    $response->assertUnprocessable()
        ->assertJsonValidationErrors(['password']);
});
