#!/bin/bash
# IdeaBrow Pipeline - Quick Status Command
# Provides instant status info in a compact format

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Default to summary mode
MODE="summary"

# Parse arguments
case "$1" in
    projects|p)
        MODE="projects"
        ;;
    phases|ph)
        MODE="phases"
        ;;
    health|h)
        MODE="health"
        ;;
    webhook|w)
        MODE="webhook"
        ;;
    full|f)
        MODE="full"
        ;;
    --help)
        echo "Usage: $0 [MODE]"
        echo ""
        echo "Modes:"
        echo "  (default)    Quick summary of all systems"
        echo "  projects|p   List active projects"
        echo "  phases|ph    Show scheduled phases"
        echo "  health|h     System health check"
        echo "  webhook|w    Webhook server status"
        echo "  full|f       Full status (all info)"
        echo ""
        echo "Examples:"
        echo "  $0           # Quick summary"
        echo "  $0 p         # Show projects"
        echo "  $0 ph        # Show phases"
        exit 0
        ;;
esac

case "$MODE" in
    summary)
        # Quick one-line summary
        PROJECTS=$(tmux list-sessions 2>/dev/null | grep -v "server\|tmux-orc" | wc -l)
        PHASES=$(ps aux | grep -E "sleep.*PHASE" | grep -v grep | wc -l)
        WEBHOOK=$(pgrep -f webhook_server.py > /dev/null && echo "UP" || echo "DOWN")
        
        if [ "$WEBHOOK" = "UP" ]; then
            WEBHOOK_COLOR=$GREEN
        else
            WEBHOOK_COLOR=$RED
        fi
        
        echo -e "${BOLD}Pipeline Status:${NC} Projects: ${CYAN}$PROJECTS${NC} | Scheduled: ${YELLOW}$PHASES${NC} | Webhook: ${WEBHOOK_COLOR}$WEBHOOK${NC}"
        ;;
        
    projects)
        echo -e "${BOLD}Active Projects:${NC}"
        tmux list-sessions 2>/dev/null | grep -v "server\|tmux-orc" | while read session; do
            NAME=$(echo "$session" | cut -d: -f1)
            
            # Check for current phase
            TRACKER="/home/wv3/ideabrow-pipeline/webhook-server/state/${NAME}_tracker.json"
            if [ -f "$TRACKER" ]; then
                PHASE=$(python3 -c "
import json
with open('$TRACKER') as f:
    t = json.load(f)
    for p in t.get('phases', []):
        if p.get('status') == 'in_progress':
            print(f\"Phase {p.get('phase_number', '?')}\")
            break
" 2>/dev/null)
                [ -z "$PHASE" ] && PHASE="Idle"
            else
                PHASE="No tracker"
            fi
            
            echo -e "  ${CYAN}$NAME${NC} - $PHASE"
        done
        ;;
        
    phases)
        echo -e "${BOLD}Scheduled Phases:${NC}"
        ps aux | grep -E "sleep.*PHASE" | grep -v grep | while read line; do
            if [[ "$line" =~ sleep[[:space:]]+([0-9]+) ]] && [[ "$line" =~ ([^[:space:]]+):0.*PHASE[[:space:]]+([0-9]+) ]]; then
                SECONDS="${BASH_REMATCH[1]}"
                PROJECT="${BASH_REMATCH[2]}"
                PHASE="${BASH_REMATCH[3]}"
                MINUTES=$((SECONDS / 60))
                
                if [ $MINUTES -lt 5 ]; then
                    COLOR=$RED
                elif [ $MINUTES -lt 15 ]; then
                    COLOR=$YELLOW
                else
                    COLOR=$GREEN
                fi
                
                echo -e "  ${CYAN}$PROJECT${NC} Phase $PHASE in ${COLOR}${MINUTES}m${NC}"
            fi
        done | head -5  # Show max 5
        ;;
        
    health)
        echo -e "${BOLD}System Health:${NC}"
        
        # Webhook
        pgrep -f webhook_server.py > /dev/null && echo -e "  Webhook: ${GREEN}✓${NC}" || echo -e "  Webhook: ${RED}✗${NC}"
        
        # Disk
        DISK=$(df -h /home/wv3 | awk 'NR==2 {print $5}' | sed 's/%//')
        if [ "$DISK" -lt "80" ]; then
            echo -e "  Disk: ${GREEN}${DISK}%${NC}"
        else
            echo -e "  Disk: ${YELLOW}${DISK}%${NC}"
        fi
        
        # Memory
        MEM=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
        if [ "$MEM" -lt "80" ]; then
            echo -e "  Memory: ${GREEN}${MEM}%${NC}"
        else
            echo -e "  Memory: ${YELLOW}${MEM}%${NC}"
        fi
        
        # Sessions
        SESSIONS=$(tmux list-sessions 2>/dev/null | wc -l)
        echo -e "  Sessions: ${CYAN}$SESSIONS${NC}"
        ;;
        
    webhook)
        if pgrep -f webhook_server.py > /dev/null; then
            echo -e "${BOLD}Webhook Server: ${GREEN}Running${NC}"
            
            # Show recent webhooks
            LOG="/home/wv3/ideabrow-pipeline/webhook-server/logs/webhook.log"
            if [ -f "$LOG" ]; then
                echo "Recent activity:"
                tail -5 "$LOG" | grep "Processing webhook" | tail -3 | while read line; do
                    if [[ "$line" =~ ([0-9]{4}-[0-9]{2}-[0-9]{2}[[:space:]]+[0-9]{2}:[0-9]{2}:[0-9]{2}) ]]; then
                        TIME="${BASH_REMATCH[1]}"
                        echo -e "  ${CYAN}$TIME${NC}"
                    fi
                done
            fi
        else
            echo -e "${BOLD}Webhook Server: ${RED}Not Running${NC}"
            echo "Start with: cd /home/wv3/ideabrow-pipeline/webhook-server && ./start_server.sh"
        fi
        ;;
        
    full)
        # Full status - call all modes
        $0 summary
        echo ""
        $0 projects
        echo ""
        $0 phases
        echo ""
        $0 health
        ;;
esac