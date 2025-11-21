import multiprocessing

# Bind to localhost (Nginx will proxy)
bind = "127.0.0.1:8000"

# Worker configuration
workers = multiprocessing.cpu_count() * 2 + 1
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

# Timeout
timeout = 120

# Daemon mode
daemon = False
