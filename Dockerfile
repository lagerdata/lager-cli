FROM python:3.8-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get install -y gcc

ADD . /app
WORKDIR /app
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install .

FROM python:3.8-slim-buster
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install -y ca-certificates && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

COPY --from=0 /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/site-packages
COPY --from=0 /usr/local/bin/lager /usr/local/bin
RUN useradd appuser
USER appuser
