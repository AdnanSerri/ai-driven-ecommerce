# ==========================================================================
# Laravel Backend - FrankenPHP + Octane
# ==========================================================================
# High-performance PHP application server
#
# Build:  docker-compose build
# Run:    docker-compose up -d
# ==========================================================================

FROM dunglas/frankenphp:latest-php8.3-alpine

# Install PHP extensions required by Laravel
RUN install-php-extensions \
    pcntl \
    pdo_pgsql \
    pgsql \
    redis \
    intl \
    zip \
    bcmath \
    opcache \
    gd

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Set working directory
WORKDIR /app

# Copy composer files first for better caching
COPY composer.json composer.lock ./

# Install dependencies (no dev in production)
RUN composer install --no-dev --no-scripts --no-autoloader --prefer-dist

# Copy application code
COPY . .

# Generate optimized autoloader
RUN composer dump-autoload --optimize

# Set permissions for Laravel storage and cache
RUN chown -R www-data:www-data /app/storage /app/bootstrap/cache \
    && chmod -R 775 /app/storage /app/bootstrap/cache

# Expose Octane port (8002 - NestJS uses 8000, ML uses 8001)
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8002/up || exit 1

# Start Octane with FrankenPHP
CMD ["php", "artisan", "octane:start", "--server=frankenphp", "--host=0.0.0.0", "--port=8002"]
