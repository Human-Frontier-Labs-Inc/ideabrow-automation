#!/bin/bash
# IdeaBrow Pipeline - Cleanup Tool
# Removes orphaned processes, duplicate schedules, and stale sessions

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

DRY_RUN=false
VERBOSE=false
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --force|-f)
            FORCE=true
            shift
            ;;
        --help|-h)
            echo -e "${BOLD}IdeaBrow Pipeline - Cleanup Tool${NC}"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -n, --dry-run    Show what would be cleaned without doing it"
            echo "  -v, --verbose    Show detailed information"
            echo "  -f, --force      Force cleanup without confirmation"
            echo "  -h, --help       Show this help message"
            echo ""
            echo "This tool cleans up:"
            echo "  • Duplicate scheduled phases"
            echo "  • Orphaned sleep processes"
            echo "  • Stale tmux sessions (no Claude running)"
            echo "  • Old state files (> 7 days)"
            echo "  • Excessive log files"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}${BOLD}              IDEABROW PIPELINE - CLEANUP TOOL${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}${BOLD}                    [DRY RUN MODE]${NC}"
fi
echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo ""

TOTAL_CLEANED=0

# Function to execute or simulate command
execute_cmd() {
    local cmd="$1"
    local desc="$2"
    
    if [ "$VERBOSE" = true ]; then
        echo -e "  ${DIM}Command: $cmd${NC}"
    fi
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "  ${YELLOW}[DRY RUN] Would: $desc${NC}"
        return 0
    else
        eval "$cmd"
        if [ $? -eq 0 ]; then
            echo -e "  ${GREEN}✓ $desc${NC}"
            TOTAL_CLEANED=$((TOTAL_CLEANED + 1))
            return 0
        else
            echo -e "  ${RED}✗ Failed: $desc${NC}"
            return 1
        fi
    fi
}

# 1. Clean duplicate scheduled phases
echo -e "${BOLD}1. Checking for duplicate scheduled phases...${NC}"

# Find all scheduled phase processes
PHASE_PROCS=$(ps aux | grep -E "sleep.*PHASE" | grep -v grep)

if [ ! -z "$PHASE_PROCS" ]; then
    # Build associative array of project-phase combinations
    declare -A phase_pids
    
    while IFS= read -r line; do
        PID=$(echo "$line" | awk '{print $2}')
        
        # Extract project and phase
        if [[ "$line" =~ ([^[:space:]]+):0.*PHASE[[:space:]]+([0-9]+) ]]; then
            PROJECT="${BASH_REMATCH[1]}"
            PHASE="${BASH_REMATCH[2]}"
            KEY="${PROJECT}-phase-${PHASE}"
            
            if [ ! -z "${phase_pids[$KEY]}" ]; then
                # Duplicate found - kill the newer one
                echo -e "  ${YELLOW}Found duplicate: $PROJECT Phase $PHASE (PID: $PID)${NC}"
                execute_cmd "kill $PID 2>/dev/null" "Removed duplicate schedule for $PROJECT Phase $PHASE"
            else
                phase_pids[$KEY]=$PID
            fi
        fi
    done <<< "$PHASE_PROCS"
else
    echo -e "  ${GREEN}No scheduled phases found${NC}"
fi
echo ""

# 2. Clean orphaned sleep processes
echo -e "${BOLD}2. Checking for orphaned sleep processes...${NC}"

# Get all sleep processes older than 24 hours
OLD_SLEEPS=$(ps aux | grep "sleep [0-9]" | grep -v grep | awk '{
    # Check if process is older than 24 hours
    cmd = "ps -o etimes= -p " $2
    cmd | getline elapsed
    close(cmd)
    if (elapsed > 86400) print $2
}')

if [ ! -z "$OLD_SLEEPS" ]; then
    COUNT=$(echo "$OLD_SLEEPS" | wc -l)
    echo -e "  ${YELLOW}Found $COUNT old sleep processes (>24 hours)${NC}"
    
    for PID in $OLD_SLEEPS; do
        execute_cmd "kill $PID 2>/dev/null" "Killed old sleep process $PID"
    done
else
    echo -e "  ${GREEN}No orphaned sleep processes found${NC}"
fi
echo ""

# 3. Clean stale tmux sessions
echo -e "${BOLD}3. Checking for stale tmux sessions...${NC}"

SESSIONS=$(tmux list-sessions 2>/dev/null | cut -d: -f1)
STALE_COUNT=0

for session in $SESSIONS; do
    # Skip system sessions
    if [[ "$session" == "server" ]] || [[ "$session" == "tmux-orc" ]]; then
        continue
    fi
    
    # Check if Claude is running
    PANE_CMD=$(tmux list-panes -t "$session:0" -F "#{pane_current_command}" 2>/dev/null | head -1)
    
    if [[ "$PANE_CMD" != *"claude"* ]]; then
        # Check if session is idle for more than 2 hours
        IDLE_TIME=$(tmux display -t "$session" -p '#{session_activity}' 2>/dev/null)
        CURRENT_TIME=$(date +%s)
        
        if [ ! -z "$IDLE_TIME" ]; then
            IDLE_SECONDS=$((CURRENT_TIME - IDLE_TIME))
            IDLE_HOURS=$((IDLE_SECONDS / 3600))
            
            if [ $IDLE_HOURS -gt 2 ]; then
                echo -e "  ${YELLOW}Stale session: $session (idle for $IDLE_HOURS hours, no Claude)${NC}"
                
                if [ "$FORCE" = true ] || [ "$DRY_RUN" = true ]; then
                    execute_cmd "tmux kill-session -t '$session' 2>/dev/null" "Removed stale session $session"
                    STALE_COUNT=$((STALE_COUNT + 1))
                else
                    echo -e "  ${CYAN}Use --force to remove stale sessions${NC}"
                fi
            fi
        fi
    fi
done

if [ $STALE_COUNT -eq 0 ] && [ "$VERBOSE" = true ]; then
    echo -e "  ${GREEN}No stale sessions found${NC}"
fi
echo ""

# 4. Clean old state files
echo -e "${BOLD}4. Checking for old state files...${NC}"

STATE_DIR="/home/wv3/ideabrow-pipeline/webhook-server/state"
if [ -d "$STATE_DIR" ]; then
    # Find state files older than 7 days
    OLD_FILES=$(find "$STATE_DIR" -name "*.json" -type f -mtime +7 2>/dev/null)
    
    if [ ! -z "$OLD_FILES" ]; then
        COUNT=$(echo "$OLD_FILES" | wc -l)
        echo -e "  ${YELLOW}Found $COUNT state files older than 7 days${NC}"
        
        for FILE in $OLD_FILES; do
            # Check if corresponding session exists
            BASENAME=$(basename "$FILE")
            SESSION_NAME=$(echo "$BASENAME" | sed 's/_.*//') 
            
            if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
                execute_cmd "rm '$FILE'" "Removed old state file: $BASENAME"
            elif [ "$VERBOSE" = true ]; then
                echo -e "  ${DIM}Keeping $BASENAME (session still active)${NC}"
            fi
        done
    else
        echo -e "  ${GREEN}No old state files found${NC}"
    fi
else
    echo -e "  ${YELLOW}State directory not found${NC}"
fi
echo ""

# 5. Clean excessive log files
echo -e "${BOLD}5. Checking log files...${NC}"

LOGS_DIR="/home/wv3/ideabrow-pipeline/webhook-server/logs"
if [ -d "$LOGS_DIR" ]; then
    # Check webhook.log size
    WEBHOOK_LOG="$LOGS_DIR/webhook.log"
    if [ -f "$WEBHOOK_LOG" ]; then
        SIZE=$(du -m "$WEBHOOK_LOG" | cut -f1)
        if [ $SIZE -gt 100 ]; then
            echo -e "  ${YELLOW}webhook.log is ${SIZE}MB (>100MB)${NC}"
            
            if [ "$FORCE" = true ] || [ "$DRY_RUN" = true ]; then
                # Keep last 10000 lines
                execute_cmd "tail -n 10000 '$WEBHOOK_LOG' > '${WEBHOOK_LOG}.tmp' && mv '${WEBHOOK_LOG}.tmp' '$WEBHOOK_LOG'" \
                           "Truncated webhook.log to last 10000 lines"
            else
                echo -e "  ${CYAN}Use --force to truncate large log files${NC}"
            fi
        else
            echo -e "  ${GREEN}webhook.log size OK (${SIZE}MB)${NC}"
        fi
    fi
    
    # Clean old session logs
    OLD_LOGS=$(find "$LOGS_DIR" -type d -mtime +7 2>/dev/null | grep -E "[0-9a-f]{8}-[0-9a-f]{4}")
    if [ ! -z "$OLD_LOGS" ]; then
        COUNT=$(echo "$OLD_LOGS" | wc -l)
        echo -e "  ${YELLOW}Found $COUNT old session log directories${NC}"
        
        for DIR in $OLD_LOGS; do
            execute_cmd "rm -rf '$DIR'" "Removed old log directory: $(basename $DIR)"
        done
    fi
else
    echo -e "  ${YELLOW}Logs directory not found${NC}"
fi
echo ""

# 6. Summary
echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}${BOLD}DRY RUN COMPLETE${NC}"
    echo -e "${YELLOW}No changes were made. Remove --dry-run to execute cleanup.${NC}"
else
    if [ $TOTAL_CLEANED -gt 0 ]; then
        echo -e "${GREEN}${BOLD}✅ CLEANUP COMPLETE${NC}"
        echo -e "${GREEN}Cleaned $TOTAL_CLEANED items${NC}"
    else
        echo -e "${GREEN}${BOLD}✅ SYSTEM CLEAN${NC}"
        echo -e "${GREEN}No cleanup needed${NC}"
    fi
fi

echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Show current status
echo -e "${BOLD}Current System Status:${NC}"
ACTIVE_SESSIONS=$(tmux list-sessions 2>/dev/null | wc -l)
SCHEDULED_PHASES=$(ps aux | grep -E "sleep.*PHASE" | grep -v grep | wc -l)
STATE_FILES=$(ls -1 "$STATE_DIR"/*.json 2>/dev/null | wc -l)

echo -e "  • Active tmux sessions: $ACTIVE_SESSIONS"
echo -e "  • Scheduled phases: $SCHEDULED_PHASES"
echo -e "  • State files: $STATE_FILES"
echo ""