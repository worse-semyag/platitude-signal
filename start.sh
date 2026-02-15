#!/bin/bash

# Start both services in background
python ./signalbot/bot.py &
PID1=$!

python ./app/app.py &
PID2=$!

# Wait for processes to complete
wait $PID1 $PID2
