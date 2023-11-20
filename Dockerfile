FROM python:3.11.5-alpine3.18
RUN apk add --no-cache --update \
    python3 python3-dev gcc \
    gfortran musl-dev \
    libffi-dev openssl-dev
RUN pip install numpy scipy
RUN pip install --upgrade pip
WORKDIR /app
COPY requirement.txt /app
RUN pip install -r requirement.txt
COPY . /app
CMD python app.py
