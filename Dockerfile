# MIT License
#
# Copyright (c) 2025 Backblaze, Inc.
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

# See https://github.com/alexdmoss/distroless-python
FROM al3xos/python-builder:3.12-debian12 AS python-base

FROM gcr.io/distroless/base-debian12:nonroot

LABEL authors="pat@backblaze.com"
LABEL org.opencontainers.image.source="https://github.com/backblaze-b2-samples/ai-rag-app"
LABEL org.opencontainers.image.description="Create a conversational AI chatbot web app that answers questions based on data stored in a Backblaze B2 bucket"

# Python etc
COPY --from=python-base /usr/local/lib/ /usr/local/lib/
COPY --from=python-base /usr/local/bin/python /usr/local/bin/
COPY --from=python-base /etc/ld.so.cache /etc/
COPY --from=python-base /usr/lib/locale/ /usr/lib/locale/

# Minimal tools for build - we'll delete them later
COPY --from=python-base /bin/echo /bin/ln /bin/rm /bin/sh /bin/chown /bin/

# Need to be root to create soft links in /lib and /usr/lib
USER root

# Shenanigans to make multi-platform builds work!
# Libraries are located in /lib/amd64-linux-gnu or /lib/aarch64-linux-gnu depending on the platform
# The problem is, there is no easy way to refer to aarch64 - ${TARGETARCH} is set to arm64 even if
# you specify linux/aarch64 as the target platform
RUN ln -s /lib/*64-linux-gnu /lib/CHIPSET_ARCH \
  && ln -s /usr/lib/*64-linux-gnu /usr/lib/CHIPSET_ARCH

# Copy required libraries
COPY --from=python-base "/lib/*64-linux-gnu/libexpat*" /lib/CHIPSET_ARCH/
COPY --from=python-base "/lib/*64-linux-gnu/libz.so.1" /lib/CHIPSET_ARCH/
COPY --from=python-base "/lib/*64-linux-gnu/libgcc_s.so.1" /lib/CHIPSET_ARCH/
COPY --from=python-base "/lib/*64-linux-gnu/libstdc++.so.6" /lib/CHIPSET_ARCH/

COPY --from=python-base "/usr/lib/*64-linux-gnu/libffi*" /usr/lib/CHIPSET_ARCH/
COPY --from=python-base "/usr/lib/*64-linux-gnu/libsqlite3.so.0" /usr/lib/CHIPSET_ARCH/
COPY --from=python-base "/usr/lib/*64-linux-gnu/libgcc_s.so.1" /usr/lib/CHIPSET_ARCH/
COPY --from=python-base "/usr/lib/*64-linux-gnu/libstdc++.so.6" /usr/lib/CHIPSET_ARCH/

WORKDIR /app

COPY --chown=python:python ./requirements.txt requirements.txt

# Do all of this in one RUN to minimize number of layers and speed up build time
RUN rm /lib/CHIPSET_ARCH /usr/lib/CHIPSET_ARCH \
  && echo "python:x:1000:python" >> /etc/group \
  && echo "python:x:1001:" >> /etc/group \
  && echo "python:x:1000:1001::/home/python:" >> /etc/passwd \
  && python --version \
  && ln -s /usr/local/bin/python /usr/local/bin/python3 \
  && python -m pip install --upgrade pip \
  && python -m pip install --no-cache-dir --upgrade -r requirements.txt \
  && chown python:python -R /app \
  && rm /bin/echo /bin/ln /bin/rm /bin/sh /bin/chown

COPY --chown=python:python . .

# standardise on locale, don't generate .pyc, enable tracebacks on seg faults
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1

# Gunicorn stuff
ARG LOGLEVEL="DEBUG"
ARG GUNICORN_LOGLEVEL="debug"
ENV GUNICORN_LOGLEVEL="${GUNICORN_LOGLEVEL}" \
    PYTHONUNBUFFERED="true" \
    PYTHONPATH="." \
    PATH="${PATH}:/home/python/.local/bin" \
    USER="python"

# Send the equivalent of a ctrl-c when stopping the container so app shuts down gracefully
STOPSIGNAL SIGINT

# config/gunicorn.py defaults port to 8000
EXPOSE 8000

# default to running as non-root, uid=1000
USER python

CMD ["gunicorn", "--pythonpath", "b2_iconik_plugin", "-b", "localhost:8000", "-w", "4", "plugin:app"]
