<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Third Party Services
    |--------------------------------------------------------------------------
    |
    | This file is for storing the credentials for third party services such
    | as Mailgun, Postmark, AWS and more. This file provides the de facto
    | location for this type of information, allowing packages to have
    | a conventional file to locate the various service credentials.
    |
    */

    'postmark' => [
        'key' => env('POSTMARK_API_KEY'),
    ],

    'resend' => [
        'key' => env('RESEND_API_KEY'),
    ],

    'ses' => [
        'key' => env('AWS_ACCESS_KEY_ID'),
        'secret' => env('AWS_SECRET_ACCESS_KEY'),
        'region' => env('AWS_DEFAULT_REGION', 'us-east-1'),
    ],

    'slack' => [
        'notifications' => [
            'bot_user_oauth_token' => env('SLACK_BOT_USER_OAUTH_TOKEN'),
            'channel' => env('SLACK_BOT_USER_DEFAULT_CHANNEL'),
        ],
    ],

    'ml' => [
        'url' => env('ML_SERVICE_URL', 'http://localhost:8001'),
        'token' => env('ML_SERVICE_AUTH_TOKEN', 'dev-token-change-in-production'),
        'timeout' => env('ML_SERVICE_TIMEOUT', 5),
        'connect_timeout' => env('ML_SERVICE_CONNECT_TIMEOUT', 2),
        'retry_times' => env('ML_SERVICE_RETRY_TIMES', 2),
        'retry_sleep' => env('ML_SERVICE_RETRY_SLEEP', 100),
    ],

];
