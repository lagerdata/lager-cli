FROM python:3.8-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get install -y gcc

ADD . /app
WORKDIR /app
RUN pip install .

RUN useradd appuser && chown -R appuser /app
USER appuser
