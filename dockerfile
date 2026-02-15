# syntax=docker/dockerfile:1

FROM python:3.13-slim-bullseye

WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN apt-get update -y && python -m pip install --upgrade pip && pip install -r requirements.txt

# Copy all application files
COPY . .
COPY start.sh ./start.sh
COPY .env  
# Make sure start.sh is executable
RUN chmod +x ./start.sh

CMD ["./start.sh"]
