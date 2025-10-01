#!/bin/bash
#
# Cron-compatible health check script
#
# This script can be added to crontab for automated monitoring:
# Check every 5 minutes
# */5 * * * * /path/to/reddit-bot/app/scripts/cron_health_check.sh
#
# Check every hour with email alerts
# 0 * * * * /path/to/reddit-bot/app/scripts/cron_health_check.sh --alerts
#

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ROOT_DIR="$(dirname "$PROJECT_DIR")"

# Change to project root directory
cd "$ROOT_DIR"

# Set Python path
export PYTHONPATH="$ROOT_DIR"

# Default configuration
API_BASE="http://localhost/api"
LOG_FILE="$ROOT_DIR/health_monitor.log"
REPORT_FILE="$ROOT_DIR/health_report_$(date +%Y%m%d_%H%M%S).json"

# Parse arguments
SEND_ALERTS=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --alerts)
            SEND_ALERTS=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --api-base)
            API_BASE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--alerts] [--verbose] [--api-base URL]"
            exit 1
            ;;
    esac
done

# Build command
CMD="python app/scripts/health_monitor.py --api-base $API_BASE --json --save \"$REPORT_FILE\""

if [ "$SEND_ALERTS" = false ]; then
    CMD="$CMD --no-alerts"
fi

if [ "$VERBOSE" = false ]; then
    CMD="$CMD --quiet"
fi

# Run health check
echo "$(date): Running health check..." >> "$LOG_FILE"

if eval $CMD >> "$LOG_FILE" 2>&1; then
    echo "$(date): Health check completed successfully" >> "$LOG_FILE"
    EXIT_CODE=0
else
    echo "$(date): Health check found critical issues" >> "$LOG_FILE"
    EXIT_CODE=1
fi

# Clean up old report files (keep last 24 hours)
find "$ROOT_DIR" -name "health_report_*.json" -type f -mtime +1 -delete 2>/dev/null

# If verbose mode, show the results
if [ "$VERBOSE" = true ]; then
    echo "Health check completed. Report saved to: $REPORT_FILE"
    if [ -f "$REPORT_FILE" ]; then
        python -c "
import json
with open('$REPORT_FILE', 'r') as f:
    data = json.load(f)
print(f\"Status: {data.get('overall_status', 'unknown').upper()}\")
print(f\"Issues: {data.get('issues_found', 0)} ({data.get('critical_issues', 0)} critical)\")
if data.get('issues'):
    print('Issues found:')
    for issue in data['issues']:
        print(f\"  - {issue['component']}: {issue['message']}\")
"
    fi
fi

exit $EXIT_CODE