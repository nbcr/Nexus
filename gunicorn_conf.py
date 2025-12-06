import multiprocessing

# Bind to localhost (Nginx will proxy)
bind = "127.0.0.1:8000"

# Worker configuration - using 1 worker to minimize memory
# Uvicorn with async/await handles concurrent requests efficiently without multiple workers
workers = 1
worker_class = "uvicorn.workers.UvicornWorker"

# Logging
accesslog = "/home/nexus/nexus/logs/access.log"
errorlog = "/home/nexus/nexus/logs/error.log"
loglevel = "info"

# Process naming
proc_name = "nexus-api"

# Restart workers after this many requests (prevent memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Timeout - worker will be killed and restarted if it exceeds this
timeout = 120

# Graceful timeout - give worker 30s to shutdown gracefully before force kill
graceful_timeout = 30

# Daemon mode
daemon = False
