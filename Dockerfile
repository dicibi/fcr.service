FROM python:latest

LABEL org.opencontainers.image.source = "https://github.com/dicibi/fcr.service"

RUN apt-get -y update && apt-get install -y --fix-missing \
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
    && apt-get clean && rm -rf /tmp/* /var/tmp/*

RUN cd ~ && \
    mkdir -p dlib && \
    git clone -b 'v19.24.2' --single-branch https://github.com/davisking/dlib.git dlib/ && \
    cd  dlib/ && \
    python3 setup.py install

WORKDIR /app
COPY requirement.txt /app
RUN pip install -r requirement.txt

COPY *.py /app

RUN mkdir -p /app/dataset && \
    mkdir -p /app/models && \
    mkdir -p /app/temporary && \
    mkdir -p /app/db

RUN rm -rf /var/lib/apt/lists/*  && \
    rm -rf /tmp/* /var/tmp/* && \
    rm -rf ~/* && \
    rm -rf ~/.cache/pip

CMD [ "gunicorn", "-b", "0.0.0.0:5000", "app:app"]