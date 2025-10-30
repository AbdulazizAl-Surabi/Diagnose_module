#!/bin/bash

# IP-Adresse und Port von Redis
REDIS_HOST="9.59.199.189"
REDIS_PORT="6379"

# Stoppen und Löschen aller Container
echo "Stopping and removing all containers..."
docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)

# Löschen aller Docker-Images
echo "Removing all Docker images..."
docker rmi $(docker images -q) --force

# Redis FLUSHALL ausführen
echo "Flushing all Redis databases..."
redis-cli -h $REDIS_HOST -p $REDIS_PORT FLUSHALL

echo "Cleanup complete!"
