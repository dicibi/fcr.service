FROM python:slim

LABEL org.opencontainers.image.source=https://github.com/dicibi/fcr.service

WORKDIR /app

COPY requirement.txt /app

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y update \
    && apt-get install -y --fix-missing \
    build-essential \
    cmake \
    gfortran \
    wget \
    curl \
    # graphicsmagick \
    # libgraphicsmagick1-dev \
    libatlas-base-dev \
    # libgtk2.0-dev \
    libjpeg-dev \
    liblapack-dev \
    # libswscale-dev \
    pkg-config \
    software-properties-common \
    zip \
    supervisor \
    python3-distutils \
    # build dlib
    && cd ~ \
    && wget https://github.com/davisking/dlib/archive/refs/tags/v19.24.6.tar.gz \
    && tar -xvzf v19.24.6.tar.gz \
    && rm v19.24.6.tar.gz \
    && mv dlib-19.24.6 dlib \
    && cd dlib && mkdir build && cd build \
    && if grep -q avx /proc/cpuinfo; then \
        cmake -D DLIB_NO_GUI_SUPPORT=ON -D USE_AVX_INSTRUCTIONS=ON ..; \
    else \
        cmake -D DLIB_NO_GUI_SUPPORT=ON ..; \
    fi \
    && cmake --build . \
    && cd .. \
    && python -m venv venv \
    && pip install build \
    && python -m build --wheel \
    && pip install dist/$(ls dist) \
    && cd .. \
    && rm -rf dlib \
    # build face_recognition
    && cd /app \
    && pip install -v -r requirement.txt \ 
    && apt-get autoremove -y build-essential cmake gfortran pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/* \
    && rm -rf ~/* \
    && rm -rf ~/.cache/pip \
    && mkdir -p /app/dataset \
    && mkdir -p /app/models \
    && mkdir -p /app/temporary \
    && mkdir -p /app/db

COPY *.py /app

STOPSIGNAL SIGTERM

COPY supervisor /etc/supervisor

ENV REDIS_URL=redis://redis:6379/0

ENV FCR_WORKERS=1
ENV FCR_TIMEOUT=50

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
