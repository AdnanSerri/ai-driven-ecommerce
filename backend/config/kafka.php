<?php

return [
    /*
    |--------------------------------------------------------------------------
    | Kafka Enabled
    |--------------------------------------------------------------------------
    |
    | This option controls whether Kafka event publishing is enabled.
    | Set to false to disable all Kafka publishing without breaking the app.
    |
    */
    'enabled' => env('KAFKA_ENABLED', true),

    /*
    |--------------------------------------------------------------------------
    | Kafka Brokers
    |--------------------------------------------------------------------------
    |
    | A comma-separated list of Kafka broker addresses.
    |
    */
    'brokers' => env('KAFKA_BROKERS', 'localhost:29092'),

    /*
    |--------------------------------------------------------------------------
    | Connection Timeout
    |--------------------------------------------------------------------------
    |
    | The timeout in seconds for connecting to Kafka brokers.
    |
    */
    'timeout' => env('KAFKA_TIMEOUT', 3),

    /*
    |--------------------------------------------------------------------------
    | Retry Configuration
    |--------------------------------------------------------------------------
    |
    | Number of retry attempts and sleep time between retries in milliseconds.
    |
    */
    'retry_times' => env('KAFKA_RETRY_TIMES', 3),
    'retry_sleep' => env('KAFKA_RETRY_SLEEP', 100),

    /*
    |--------------------------------------------------------------------------
    | Topics
    |--------------------------------------------------------------------------
    |
    | Mapping of event types to Kafka topic names.
    |
    */
    'topics' => [
        'order_completed' => 'order.completed',
        'review_created' => 'review.created',
        'user_interaction' => 'user.interaction',
        'cart_updated' => 'cart.updated',
    ],
];
