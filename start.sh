#!/bin/bash

# Load environment variables once
set -a
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found"
    exit 1
fi
set +a

# Start both services in background
python3 ./signalbot/bot.py &
PID1=$!

python3 ./app/app.py &
PID2=$!

# Wait for processes to complete
wait $PID1 $PID2
