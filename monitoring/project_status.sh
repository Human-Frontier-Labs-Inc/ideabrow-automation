#!/bin/bash
# IdeaBrow Pipeline - Detailed Project Status Viewer
# Shows comprehensive status for a specific project or all projects

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# Configuration
STATE_DIR="/home/wv3/ideabrow-pipeline/webhook-server/state"
LOGS_DIR="/home/wv3/ideabrow-pipeline/webhook-server/logs"

show_project_details() {
    local project_name=$1
    
    echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}${BOLD}Project: $project_name${NC}"
    echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Check if tmux session exists
    if tmux has-session -t "$project_name" 2>/dev/null; then
        echo -e "${GREEN}✅ Session Status: ACTIVE${NC}"
        
        # Get pane info
        PANE_CMD=$(tmux list-panes -t "$project_name:0" -F "#{pane_current_command}" 2>/dev/null | head -1)
        if [[ "$PANE_CMD" == *"claude"* ]]; then
            echo -e "${GREEN}✅ Claude Code: RUNNING${NC}"
        else
            echo -e "${YELLOW}⚠️  Claude Code: NOT DETECTED (pane cmd: $PANE_CMD)${NC}"
        fi
        
        # Show last 5 lines from tmux pane
        echo -e "\n${BOLD}Recent Activity:${NC}"
        echo -e "${DIM}────────────────────────────────────────────────────${NC}"
        tmux capture-pane -t "$project_name:0" -p -S -5 2>/dev/null | sed 's/^/  /'
        echo -e "${DIM}────────────────────────────────────────────────────${NC}"
    else
        echo -e "${RED}❌ Session Status: NOT FOUND${NC}"
    fi
    
    # Check state file
    STATE_FILE="$STATE_DIR/${project_name}_state.json"
    if [ -f "$STATE_FILE" ]; then
        echo -e "\n${BOLD}State Information:${NC}"
        
        # Parse JSON using Python for reliability
        python3 -c "
import json
import sys
from datetime import datetime

try:
    with open('$STATE_FILE') as f:
        data = json.load(f)
    
    print(f'  Created: {data.get(\"timestamp\", \"Unknown\")}')
    print(f'  Repo URL: {data.get(\"repo_url\", \"Not set\")}')
    print(f'  Template: {data.get(\"template\", \"None\")}')
    
    # Calculate age
    if 'timestamp' in data:
        try:
            created = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            age = datetime.now() - created.replace(tzinfo=None)
            hours = int(age.total_seconds() / 3600)
            mins = int((age.total_seconds() % 3600) / 60)
            print(f'  Age: {hours}h {mins}m')
        except:
            pass
            
except Exception as e:
    print(f'  Error reading state: {e}')
" 2>/dev/null || echo -e "  ${RED}Error parsing state file${NC}"
    else
        echo -e "\n${YELLOW}⚠️  No state file found${NC}"
    fi
    
    # Check tracker file for phases
    TRACKER_FILE="$STATE_DIR/${project_name}_tracker.json"
    if [ -f "$TRACKER_FILE" ]; then
        echo -e "\n${BOLD}Phase Progress:${NC}"
        
        python3 -c "
import json
import sys

try:
    with open('$TRACKER_FILE') as f:
        tracker = json.load(f)
    
    phases = tracker.get('phases', [])
    if not phases:
        print('  No phases defined')
    else:
        total = len(phases)
        completed = len([p for p in phases if p.get('status') == 'completed'])
        in_progress = [p for p in phases if p.get('status') == 'in_progress']
        
        print(f'  Total Phases: {total}')
        print(f'  Completed: {completed}/{total} ({int(completed/total*100)}%)')
        
        if in_progress:
            current = in_progress[0]
            print(f'  Current: Phase {current.get(\"phase_number\", \"?\")} - {current.get(\"name\", \"Unknown\")}')
        
        print('\n  Phase List:')
        for phase in phases[:10]:  # Show max 10 phases
            num = phase.get('phase_number', '?')
            name = phase.get('name', 'Unknown')[:40]
            status = phase.get('status', 'pending')
            
            if status == 'completed':
                icon = '✅'
                color = '\033[0;32m'
            elif status == 'in_progress':
                icon = '🔄'
                color = '\033[1;33m'
            else:
                icon = '⏳'
                color = '\033[2m'
            
            print(f'    {color}{icon} Phase {num}: {name}\033[0m')
            
except Exception as e:
    print(f'  Error reading tracker: {e}')
" 2>/dev/null || echo -e "  ${RED}Error parsing tracker file${NC}"
    else
        echo -e "\n${YELLOW}⚠️  No tracker file found${NC}"
    fi
    
    # Check for scheduled phases
    echo -e "\n${BOLD}Scheduled Phases:${NC}"
    SCHEDULED=$(ps aux | grep -E "sleep.*$project_name.*PHASE" | grep -v grep)
    if [ ! -z "$SCHEDULED" ]; then
        echo "$SCHEDULED" | while read line; do
            if [[ "$line" =~ sleep[[:space:]]+([0-9]+) ]]; then
                SECONDS="${BASH_REMATCH[1]}"
                MINUTES=$((SECONDS / 60))
                
                if [[ "$line" =~ PHASE[[:space:]]+([0-9]+) ]]; then
                    PHASE_NUM="${BASH_REMATCH[1]}"
                    echo -e "  ${YELLOW}⏰ Phase $PHASE_NUM scheduled in $MINUTES minutes${NC}"
                fi
            fi
        done
    else
        echo -e "  ${DIM}No phases currently scheduled${NC}"
    fi
    
    # Check for errors in webhook log
    if [ -f "$LOGS_DIR/webhook.log" ]; then
        echo -e "\n${BOLD}Recent Webhook Activity:${NC}"
        RECENT_LOGS=$(grep "$project_name" "$LOGS_DIR/webhook.log" 2>/dev/null | tail -3)
        if [ ! -z "$RECENT_LOGS" ]; then
            echo "$RECENT_LOGS" | while read line; do
                if [[ "$line" == *"ERROR"* ]]; then
                    echo -e "  ${RED}⚠ $(echo "$line" | cut -c1-70)...${NC}"
                else
                    echo -e "  ${DIM}$(echo "$line" | cut -c1-70)...${NC}"
                fi
            done
        else
            echo -e "  ${DIM}No recent webhook activity${NC}"
        fi
    fi
    
    echo ""
}

show_all_projects() {
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${BOLD}              ALL PROJECTS - QUICK OVERVIEW${NC}"
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Get all tmux sessions
    SESSIONS=$(tmux list-sessions 2>/dev/null | grep -v "server\|tmux-orc" | cut -d: -f1)
    
    if [ -z "$SESSIONS" ]; then
        echo -e "${YELLOW}No active project sessions found${NC}"
        echo ""
        
        # Check for state files without sessions
        if [ -d "$STATE_DIR" ]; then
            STATE_FILES=$(ls -1 "$STATE_DIR"/*_state.json 2>/dev/null)
            if [ ! -z "$STATE_FILES" ]; then
                echo -e "${BOLD}Orphaned State Files (sessions terminated):${NC}"
                for file in $STATE_FILES; do
                    basename "$file" | sed 's/_state.json//' | sed 's/^/  • /'
                done
            fi
        fi
    else
        # Create a summary table
        printf "${BOLD}%-20s %-10s %-15s %-30s${NC}\n" "Project" "Status" "Current Phase" "Repository"
        echo -e "${DIM}────────────────────────────────────────────────────────────────────────────${NC}"
        
        for session in $SESSIONS; do
            # Default values
            STATUS="${GREEN}Active${NC}"
            PHASE="Unknown"
            REPO="Not set"
            
            # Check if Claude is running
            PANE_CMD=$(tmux list-panes -t "$session:0" -F "#{pane_current_command}" 2>/dev/null | head -1)
            if [[ "$PANE_CMD" != *"claude"* ]]; then
                STATUS="${YELLOW}No Claude${NC}"
            fi
            
            # Get phase from tracker
            TRACKER_FILE="$STATE_DIR/${session}_tracker.json"
            if [ -f "$TRACKER_FILE" ]; then
                PHASE=$(python3 -c "
import json
try:
    with open('$TRACKER_FILE') as f:
        tracker = json.load(f)
    phases = tracker.get('phases', [])
    current = [p for p in phases if p.get('status') == 'in_progress']
    if current:
        p = current[0]
        print(f\"Phase {p.get('phase_number', '?')}\")
    else:
        completed = len([p for p in phases if p.get('status') == 'completed'])
        total = len(phases)
        if total > 0:
            print(f\"{completed}/{total} done\")
except:
    pass
" 2>/dev/null)
                [ -z "$PHASE" ] && PHASE="No phases"
            fi
            
            # Get repo from state
            STATE_FILE="$STATE_DIR/${session}_state.json"
            if [ -f "$STATE_FILE" ]; then
                REPO=$(python3 -c "
import json
try:
    with open('$STATE_FILE') as f:
        data = json.load(f)
    url = data.get('repo_url', '')
    if url:
        # Extract just the repo name
        parts = url.rstrip('/').split('/')
        if len(parts) >= 2:
            print(f'{parts[-2]}/{parts[-1]}'[:28])
except:
    pass
" 2>/dev/null)
                [ -z "$REPO" ] && REPO="Not set"
            fi
            
            printf "%-20s %-20b %-15s %-30s\n" "$session" "$STATUS" "$PHASE" "$REPO"
        done
        
        echo -e "${DIM}────────────────────────────────────────────────────────────────────────────${NC}"
        echo -e "${CYAN}Total: $(echo "$SESSIONS" | wc -l) active projects${NC}"
    fi
    
    echo ""
}

# Parse command line arguments
case "$1" in
    "")
        # No arguments - show all projects
        show_all_projects
        
        echo -e "${BOLD}Usage:${NC}"
        echo "  $0              - Show all projects (this view)"
        echo "  $0 <project>    - Show detailed info for specific project"
        echo "  $0 --help       - Show this help message"
        echo ""
        echo -e "${BOLD}Other Monitoring Tools:${NC}"
        echo "  pipeline_monitor.py      - Full dashboard with real-time updates"
        echo "  pipeline_monitor.py -w   - Watch mode (auto-refresh)"
        echo "  health_check.sh         - System health diagnostics"
        echo ""
        ;;
    
    "--help"|"-h")
        echo -e "${BOLD}IdeaBrow Pipeline - Project Status Viewer${NC}"
        echo ""
        echo "Usage:"
        echo "  $0              - Show overview of all projects"
        echo "  $0 <project>    - Show detailed status for specific project"
        echo ""
        echo "Examples:"
        echo "  $0              # List all projects"
        echo "  $0 myapp-v1     # Show details for 'myapp-v1' project"
        echo ""
        echo "This tool provides quick project status information including:"
        echo "  • Tmux session status"
        echo "  • Current phase progress"
        echo "  • Scheduled phases"
        echo "  • Recent activity"
        echo "  • Repository information"
        echo ""
        ;;
    
    *)
        # Project name provided - show details
        show_project_details "$1"
        ;;
esac