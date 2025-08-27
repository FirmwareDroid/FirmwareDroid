#!/bin/bash
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

# auto_setup.sh - Automatic setup script for FirmwareDroid
# This script creates the necessary directory structure and configuration files
# to run FirmwareDroid without requiring manual setup.py execution

set -e

echo "FirmwareDroid Auto-Setup: Starting automatic configuration..."

# Base directory (should be /var/www or wherever the container mounts the project)
BASE_DIR="${BASE_DIR:-/var/www}"
ENV_DIR="${BASE_DIR}/env"
DATA_DIR="${BASE_DIR}/data"

# Ensure we have a .env file
if [ ! -f "${BASE_DIR}/.env" ]; then
    if [ -f "${BASE_DIR}/default.env" ]; then
        echo "Using default.env as .env file"
        cp "${BASE_DIR}/default.env" "${BASE_DIR}/.env"
    else
        echo "ERROR: No .env or default.env file found!"
        exit 1
    fi
fi

# Source environment variables (skip comments and empty lines)
if [ -f "${BASE_DIR}/.env" ]; then
    echo "Loading environment variables..."
    export $(grep -v '^#' "${BASE_DIR}/.env" | grep -v '^$' | grep '=' | xargs)
fi

# Create data directories
echo "Creating data directories..."
mkdir -p "${DATA_DIR}/django_database"
mkdir -p "${DATA_DIR}/mongo_database"
for i in {00..09}; do
    mkdir -p "${DATA_DIR}/${i}_file_storage"
done

# Create env directories
echo "Creating environment directories..."
mkdir -p "${ENV_DIR}/nginx/live/${DOMAIN_NAME:-fmd.localhost}"
mkdir -p "${ENV_DIR}/redis"
mkdir -p "${ENV_DIR}/mongo/init"
mkdir -p "${ENV_DIR}/mongo/auth"

# Create Redis configuration if it doesn't exist
if [ ! -f "${ENV_DIR}/redis/redis.conf" ]; then
    echo "Creating Redis configuration..."
    cat > "${ENV_DIR}/redis/redis.conf" << 'EOF'
# Basic Redis configuration for FirmwareDroid
bind 0.0.0.0
port 6379
protected-mode yes
tcp-backlog 511
timeout 0
tcp-keepalive 300
daemonize no
supervised no
pidfile /var/run/redis_6379.pid
loglevel notice
logfile ""
databases 16
always-show-logo yes
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir ./
replica-serve-stale-data yes
replica-read-only yes
repl-diskless-sync no
repl-diskless-sync-delay 5
repl-diskless-load disabled
replica-priority 100
acllog-max-len 128
lazyfree-lazy-eviction no
lazyfree-lazy-expire no
lazyfree-lazy-server-del no
replica-lazy-flush no
lazyfree-lazy-user-del no
oom-score-adj no
oom-score-adj-values 0 200 800
appendonly no
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
aof-use-rdb-preamble yes
lua-time-limit 5000
slowlog-log-slower-than 10000
slowlog-max-len 128
latency-monitor-threshold 0
notify-keyspace-events ""
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
hll-sparse-max-bytes 3000
stream-node-max-bytes 4096
stream-node-max-entries 100
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
hz 10
dynamic-hz yes
aof-rewrite-incremental-fsync yes
rdb-save-incremental-fsync yes
jemalloc-bg-thread yes
EOF
fi

# Create MongoDB cluster key if it doesn't exist
if [ ! -f "${ENV_DIR}/mongo/auth/cluster.key" ]; then
    echo "Creating MongoDB cluster key..."
    openssl rand -base64 756 > "${ENV_DIR}/mongo/auth/cluster.key"
    chmod 400 "${ENV_DIR}/mongo/auth/cluster.key"
fi

# Create MongoDB replica set setup script if it doesn't exist
if [ ! -f "${ENV_DIR}/mongo/init/mongo_replica_set_setup.sh" ]; then
    echo "Creating MongoDB replica set setup script..."
    cat > "${ENV_DIR}/mongo/init/mongo_replica_set_setup.sh" << 'EOF'
#!/bin/bash
# MongoDB replica set initialization script for FirmwareDroid

sleep 10

mongo --host mongo-db-1:27017 -u $MONGO_INITDB_ROOT_USERNAME -p $MONGO_INITDB_ROOT_PASSWORD --authenticationDatabase admin <<EOL
use admin;
db.createUser({
    user: "$MONGODB_USERNAME",
    pwd: "$MONGODB_PASSWORD",
    roles: [
        { role: "readWrite", db: "$MONGODB_DATABASE_NAME" },
        { role: "dbAdmin", db: "$MONGODB_DATABASE_NAME" }
    ]
});

rs.initiate({
    _id: "$MONGODB_REPLICA_SET",
    members: [
        { _id: 0, host: "mongo-db-1:27017" }
    ]
});

use $MONGODB_DATABASE_NAME;
db.createCollection("init");
EOL
EOF
    chmod +x "${ENV_DIR}/mongo/init/mongo_replica_set_setup.sh"
fi

# Create self-signed SSL certificate if it doesn't exist
if [ ! -f "${ENV_DIR}/nginx/live/${DOMAIN_NAME:-fmd.localhost}/certificate.pem" ]; then
    echo "Creating self-signed SSL certificate..."
    
    # Create private key
    openssl genrsa -out "${ENV_DIR}/nginx/live/${DOMAIN_NAME:-fmd.localhost}/privkey.pem" 2048
    
    # Create certificate
    openssl req -new -x509 -key "${ENV_DIR}/nginx/live/${DOMAIN_NAME:-fmd.localhost}/privkey.pem" \
        -out "${ENV_DIR}/nginx/live/${DOMAIN_NAME:-fmd.localhost}/certificate.pem" \
        -days 1024 \
        -subj "/C=CH/ST=Zurich/L=Winterthur/O=Zurich University of Applied Sciences/CN=${DOMAIN_NAME:-fmd.localhost}"
fi

# Create nginx configuration if it doesn't exist
if [ ! -f "${ENV_DIR}/nginx/app.conf" ]; then
    echo "Creating nginx configuration..."
    cat > "${ENV_DIR}/nginx/app.conf" << EOF
server {
    #################################################
    # General Server Config http                    #
    #################################################
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name ${DOMAIN_NAME:-fmd.localhost};
    charset utf-8;
    # Security
    server_tokens off;
    if (\$request_method !~ ^(GET|HEAD|POST)\$ ) {
    return 444; }

    # Certbot TLS-Challenge
     location ~ /.well-known/acme-challenge/ {
         allow all;
         root /var/www/certbot;
         return http://\$host\$request_uri;
     }

    location ~ / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    #################################################
    # General Server Config https                   #
    #################################################
    listen [::]:443 ssl;
    listen 443 ssl;
    server_name ${DOMAIN_NAME:-fmd.localhost};
    root /usr/share/nginx/html;
    index index.html index.htm;
    # Timeout settings
    proxy_connect_timeout 600;
    proxy_send_timeout 600;
    proxy_read_timeout 600;
    send_timeout 600;
    # SSL code
    ssl_certificate /etc/letsencrypt/live/${DOMAIN_NAME:-fmd.localhost}/certificate.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN_NAME:-fmd.localhost}/privkey.pem;
    # Security
    server_tokens off;
    if (\$request_method !~ ^(GET|HEAD|POST)\$ ) {
    return 444; }
    add_header Strict-Transport-Security max-age=31536000;

    # Logging
    # error_log /usr/share/nginx/log debug;

    #################################################
    # Routing                                       #
    #################################################
    # Static files React
    location /static/ {
        root /usr/share/nginx/html/;
    }

    # Static files django
    location /django_static/ {
        root /usr/share/nginx/;
    }

    # React frontend
    location / {
        root   /usr/share/nginx/html;
        index  index.html index.htm;
        try_files \$uri \$uri/ /index.html;
    }

    # Django backend security
    location /csrf {
        try_files \$uri @proxy_api;
    }

    # Django backend REST API
    location /api-auth/ {
        try_files \$uri @proxy_api;
    }

    # Django backend
    location /download {
        try_files \$uri @proxy_api;
    }

    # Django backend
    location /upload {
        proxy_set_header Authorization \$http_authorization;
        client_max_body_size 10G;
        proxy_read_timeout 36000s;
        proxy_send_timeout 36000s;
        try_files \$uri @proxy_api;
    }

    # Django backend GraphQL API
    location /graphql {
        try_files \$uri @proxy_api;
    }

    # Django backend RQ
    location /django-rq {
        try_files \$uri @proxy_api;
    }

    # Django backend
    location @proxy_api {
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Protocol \$scheme;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_pass http://backend-worker:5000;
    }

    # Django backend
    location /admin {
        try_files \$uri @proxy_api;
    }
}
EOF
fi

echo "FirmwareDroid Auto-Setup: Configuration complete!"
echo "You can now run 'docker compose up' to start FirmwareDroid."