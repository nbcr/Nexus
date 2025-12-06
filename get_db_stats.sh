#!/bin/bash
# Database query wrapper for storage monitor

psql_query() {
    sudo -u postgres psql -d nexus -t -c "$1" 2>/dev/null
}

psql_query "SELECT pg_size_pretty(pg_database_size(current_database()));"
psql_query "SELECT COUNT(*) FROM content_items;"
