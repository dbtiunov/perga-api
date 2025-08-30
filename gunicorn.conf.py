import multiprocessing


bind = "0.0.0.0:8000"
workers = 2 #multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 30
graceful_timeout = 30
keepalive = 5
backlog = 512

accesslog = "-"
errorlog = "-"
loglevel = "debug"
