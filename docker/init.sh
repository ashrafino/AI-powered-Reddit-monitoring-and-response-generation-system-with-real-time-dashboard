#!/bin/bash

# Function to wait for a service
wait_for_service() {
    local host="$1"
    local port="$2"
    local service="$3"
    
    echo "Waiting for $service to start..."
    while ! nc -z "$host" "$port"; do
        echo "Waiting for $service..."
        sleep 1
    done
    echo "$service is ready!"
}

# Function to run database migrations
run_migrations() {
    echo "Running database migrations..."
    python -m app.scripts.db
    if [ $? -ne 0 ]; then
        echo "Failed to run migrations"
        exit 1
    fi
    echo "Migrations completed successfully"
}

# Function to create admin user
create_admin() {
    echo "Creating admin user..."
    python -m app.scripts.create_admin
    if [ $? -ne 0 ]; then
        echo "Failed to create admin user"
        exit 1
    fi
    echo "Admin user created successfully"
}

# Function to create default client
create_default_client() {
    echo "Creating default client..."
    python -m app.scripts.create_default_client
    if [ $? -ne 0 ]; then
        echo "Warning: Failed to create default client (may already exist)"
    else
        echo "Default client created successfully"
    fi
}

# Wait for PostgreSQL
wait_for_service postgres 5432 "PostgreSQL"

# Wait for Redis
wait_for_service redis 6379 "Redis"

# Run migrations
run_migrations

# Create admin user
create_admin

# Create default client
create_default_client

# Start the application
echo "Starting application..."
exec "$@"