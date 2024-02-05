FROM redis:7.2-rc-alpine

CMD redis-server --appendonly yes --requirepass $REDIS_PASSWORD --maxmemory $MAX_MEMORY --maxmemory-policy $MAX_MEMORY_POLICY