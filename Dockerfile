FROM python:latest

LABEL org.opencontainers.image.source = "https://github.com/dicibi/fcr.service"

WORKDIR /app

COPY requirement.txt /app

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y update \
    && apt-get install -y --fix-missing \
    build-essential \
    cmake \
    gfortran \
    git \
    wget \
    curl \
    graphicsmagick \
    libgraphicsmagick1-dev \
    libatlas-base-dev \
    libavcodec-dev \
    libavformat-dev \
    libgtk2.0-dev \
    libjpeg-dev \
    liblapack-dev \
    libswscale-dev \
    pkg-config \
    python3-dev \
    python3-numpy \
    software-properties-common \
    zip \
    redis \
    supervisor \
    && pip install -r requirement.txt \ 
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

CMD /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
