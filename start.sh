#!/bin/bash

# Start both services in background
python3 ./signalbot/bot.py &
PID1=$!

python3 ./app/app.py &
PID2=$!

# Wait for processes to complete
wait $PID1 $PID2
