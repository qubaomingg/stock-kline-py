#!/bin/bash

APP_NAME="stock-kline"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"

mkdir -p $LOG_DIR

start() {
    echo "Starting $APP_NAME with PM2..."
    cd $SCRIPT_DIR
    pm2 delete "$APP_NAME" 2>/dev/null || true

    if [ -d "venv" ]; then
        source venv/bin/activate
    fi

    export PYTHONPATH="$SCRIPT_DIR"

    pm2 start main.py \
        --name "$APP_NAME" \
        --interpreter ./venv/bin/python \
        --log-date-format "YYYY-MM-DD HH:mm:ss" \
        --log "$LOG_DIR/combined.log" \
        --error "$LOG_DIR/error.log" \
        --output "$LOG_DIR/out.log"

    pm2 save 2>/dev/null || true
    sleep 3
    pm2 status $APP_NAME
}

stop() {
    pm2 stop $APP_NAME 2>/dev/null || true
}

restart() {
    pm2 restart $APP_NAME 2>/dev/null || true
}

status() {
    pm2 status $APP_NAME
    pm2 logs $APP_NAME --lines 20 --nostream 2>/dev/null
}

logs() {
    pm2 logs $APP_NAME --lines 100 2>/dev/null
}

case "${1:-start}" in
    start)   start ;;
    stop)    stop ;;
    restart) restart ;;
    status)  status ;;
    logs)    logs ;;
    *)       echo "Usage: $0 {start|stop|restart|status|logs}" ;;
esac
