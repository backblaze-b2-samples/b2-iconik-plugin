# MIT License
#
# Copyright (c) 2025 Backblaze
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Listen on port 80 on all ports
bind = "0.0.0.0:80"

# Start 4 worker threads
workers = 4

# Iconik jobs can take a long time to complete!
timeout = 3600

# Use asynchronous workers via gevent
worker_class = 'gevent'

# Set the log file locations as appropriate for your environment

# Access log - records incoming HTTP requests
# accesslog = "/var/log/gunicorn.access.log"

# Error log - records Gunicorn server goings-on
# errorlog = "/var/log/gunicorn.error.log"

# Whether to send app output to the error log
capture_output = True

# How verbose the Gunicorn error logs should be
loglevel = "debug"
