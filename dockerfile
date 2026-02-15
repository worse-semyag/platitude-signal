# syntax=docker/dockerfile:1

FROM python:3.13-slim-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt
COPY . .

RUN apt-get update -y && python -m pip install --upgrade pip && pip install -r requirements.txt

CMD ["/start.sh"]