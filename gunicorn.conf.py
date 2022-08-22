# gunicorn.conf.py
# Non logging stuff
bind = "0.0.0.0:80"
workers = 4
# Iconik jobs can take a long time to complete!
timeout = 3600
# Use asynchronous workers via gevent
worker_class = 'gevent'
# Access log - records incoming HTTP requests
accesslog = "/var/log/gunicorn.access.log"
# Error log - records Gunicorn server goings-on
errorlog = "/var/log/gunicorn.error.log"
# Whether to send app output to the error log
capture_output = True
# How verbose the Gunicorn error logs should be
loglevel = "info"
