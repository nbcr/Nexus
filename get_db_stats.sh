#!/bin/bash
# Database query wrapper for storage monitor

psql_query() {
    local query="$1"
    sudo -u postgres psql -d nexus -t -c "$query" 2>/dev/null
    return 0
}

psql_query "SELECT pg_size_pretty(pg_database_size(current_database()));"
psql_query "SELECT COUNT(*) FROM content_items;"
