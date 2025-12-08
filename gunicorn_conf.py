import multiprocessing

# Bind to localhost (Nginx will proxy)
bind = "127.0.0.1:8000"

# Worker configuration - 3 workers optimal for 2 CPU cores + load balancing
# Uvicorn with async/await handles concurrent requests efficiently
# With 7.2GB RAM, can support increased concurrency
workers = 3
worker_class = "uvicorn.workers.UvicornWorker"

# Logging
accesslog = "/home/nexus/nexus/logs/access.log"
errorlog = "/home/nexus/nexus/logs/error.log"
loglevel = "info"

# Process naming
proc_name = "nexus-api"

# Restart workers after this many requests (prevent memory leaks)
# Increased for better performance with more RAM (7.2GB available)
max_requests = 5000
max_requests_jitter = 500

# Timeout - worker will be killed and restarted if it exceeds this
timeout = 120

# Graceful timeout - give worker 30s to shutdown gracefully before force kill
graceful_timeout = 30

# Daemon mode
daemon = False
