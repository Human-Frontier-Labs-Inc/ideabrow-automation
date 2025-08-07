#!/bin/bash
# IdeaBrow Pipeline - Comprehensive Health Check
# Run this before starting projects or to diagnose issues

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}${BOLD}         IDEABROW PIPELINE - COMPREHENSIVE HEALTH CHECK${NC}"
echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo ""

ISSUES=0
WARNINGS=0

# 1. Check webhook server
echo -e "${BOLD}1. Webhook Server Check...${NC}"
if pgrep -f "webhook_server.py" > /dev/null; then
    echo -e "   ${GREEN}✅ Webhook server is running${NC}"
    
    # Test the health endpoint
    if curl -s http://localhost:8091/health 2>/dev/null | grep -q "healthy"; then
        echo -e "   ${GREEN}✅ Webhook server responding to health checks${NC}"
    else
        echo -e "   ${RED}❌ Webhook server not responding properly${NC}"
        echo -e "   ${YELLOW}Fix: Check logs at /home/wv3/ideabrow-pipeline/webhook-server/logs/webhook.log${NC}"
        ISSUES=$((ISSUES + 1))
    fi
    
    # Check if port is properly bound
    if lsof -i:8091 > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ Port 8091 is properly bound${NC}"
    else
        echo -e "   ${RED}❌ Port 8091 is not bound${NC}"
        ISSUES=$((ISSUES + 1))
    fi
else
    echo -e "   ${RED}❌ Webhook server not running${NC}"
    echo -e "   ${YELLOW}Fix: cd /home/wv3/ideabrow-pipeline/webhook-server && ./start_server.sh${NC}"
    ISSUES=$((ISSUES + 1))
fi
echo ""

# 2. Check Python environment
echo -e "${BOLD}2. Python Environment Check...${NC}"
if [ -d "/home/wv3/ideabrow-pipeline/venv" ]; then
    echo -e "   ${GREEN}✅ Virtual environment exists${NC}"
    
    # Check required packages
    source /home/wv3/ideabrow-pipeline/venv/bin/activate 2>/dev/null
    MISSING_PACKAGES=""
    
    for package in flask psutil requests; do
        if ! python3 -c "import $package" 2>/dev/null; then
            MISSING_PACKAGES="$MISSING_PACKAGES $package"
        fi
    done
    
    if [ -z "$MISSING_PACKAGES" ]; then
        echo -e "   ${GREEN}✅ All required Python packages installed${NC}"
    else
        echo -e "   ${RED}❌ Missing Python packages:$MISSING_PACKAGES${NC}"
        echo -e "   ${YELLOW}Fix: source venv/bin/activate && pip install$MISSING_PACKAGES${NC}"
        ISSUES=$((ISSUES + 1))
    fi
    deactivate 2>/dev/null
else
    echo -e "   ${RED}❌ Virtual environment missing${NC}"
    echo -e "   ${YELLOW}Fix: cd /home/wv3/ideabrow-pipeline && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt${NC}"
    ISSUES=$((ISSUES + 1))
fi
echo ""

# 3. Check orchestrator scripts
echo -e "${BOLD}3. Orchestrator Scripts Check...${NC}"
ORCHESTRATOR_DIR="/home/wv3/ideabrow-pipeline/orchestrator"
SCRIPTS=(
    "send-claude-message.sh"
    "schedule_with_note.sh"
    "create_automated_session.sh"
    "monitor-app-ready.sh"
    "session-utils.sh"
)

SCRIPT_ISSUES=0
for script in "${SCRIPTS[@]}"; do
    if [ -f "$ORCHESTRATOR_DIR/$script" ]; then
        if [ -x "$ORCHESTRATOR_DIR/$script" ]; then
            echo -e "   ${GREEN}✅ $script exists and is executable${NC}"
        else
            echo -e "   ${YELLOW}⚠️  $script exists but not executable${NC}"
            echo -e "   ${YELLOW}Fix: chmod +x $ORCHESTRATOR_DIR/$script${NC}"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        echo -e "   ${RED}❌ $script missing${NC}"
        SCRIPT_ISSUES=$((SCRIPT_ISSUES + 1))
    fi
done

if [ $SCRIPT_ISSUES -gt 0 ]; then
    echo -e "   ${RED}Missing $SCRIPT_ISSUES orchestrator scripts${NC}"
    ISSUES=$((ISSUES + 1))
fi
echo ""

# 4. Check state and logs directories
echo -e "${BOLD}4. Directory Structure Check...${NC}"
REQUIRED_DIRS=(
    "/home/wv3/ideabrow-pipeline/webhook-server/state"
    "/home/wv3/ideabrow-pipeline/webhook-server/logs"
    "/home/wv3/ideabrow-pipeline/monitoring"
    "/home/wv3/ideabrow-pipeline/templates"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "   ${GREEN}✅ $(basename $dir) directory exists${NC}"
        
        # Check for files in state directory
        if [[ "$dir" == *"state"* ]]; then
            STATE_FILES=$(ls -1 $dir/*.json 2>/dev/null | wc -l)
            if [ $STATE_FILES -gt 0 ]; then
                echo -e "      ${CYAN}Found $STATE_FILES state files${NC}"
            fi
        fi
    else
        echo -e "   ${RED}❌ $(basename $dir) directory missing${NC}"
        echo -e "   ${YELLOW}Fix: mkdir -p $dir${NC}"
        ISSUES=$((ISSUES + 1))
    fi
done
echo ""

# 5. Check for zombie/duplicate processes
echo -e "${BOLD}5. Process Cleanup Check...${NC}"

# Check for duplicate scheduled phases
DUPLICATE_COUNT=$(ps aux | grep -E "sleep.*(send-claude-message|PHASE)" | grep -v grep | awk '{print $NF}' | sort | uniq -c | awk '$1 > 1' | wc -l)
if [ "$DUPLICATE_COUNT" -eq "0" ]; then
    echo -e "   ${GREEN}✅ No duplicate scheduled processes${NC}"
else
    echo -e "   ${YELLOW}⚠️  Found $DUPLICATE_COUNT duplicate scheduled processes${NC}"
    echo -e "   ${YELLOW}Fix: Run /home/wv3/ideabrow-pipeline/monitoring/cleanup_phases.sh${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Check for orphaned sleep processes
ORPHAN_COUNT=$(ps aux | grep -E "sleep [0-9]+" | grep -v grep | wc -l)
if [ "$ORPHAN_COUNT" -gt "10" ]; then
    echo -e "   ${YELLOW}⚠️  High number of sleep processes: $ORPHAN_COUNT${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "   ${GREEN}✅ Sleep process count normal: $ORPHAN_COUNT${NC}"
fi
echo ""

# 6. Check tmux sessions
echo -e "${BOLD}6. Active Sessions Check...${NC}"
if command -v tmux &> /dev/null; then
    SESSION_COUNT=$(tmux list-sessions 2>/dev/null | wc -l)
    if [ "$SESSION_COUNT" -gt "0" ]; then
        echo -e "   ${GREEN}✅ $SESSION_COUNT tmux sessions active${NC}"
        
        # List active project sessions
        PROJECTS=$(tmux list-sessions 2>/dev/null | grep -v "server\|tmux-orc" | cut -d: -f1)
        if [ ! -z "$PROJECTS" ]; then
            echo -e "   ${CYAN}Active projects:${NC}"
            for proj in $PROJECTS; do
                echo -e "      • $proj"
            done
        fi
    else
        echo -e "   ${CYAN}ℹ️  No tmux sessions active (normal if no projects running)${NC}"
    fi
else
    echo -e "   ${RED}❌ tmux not installed${NC}"
    echo -e "   ${YELLOW}Fix: sudo apt-get install tmux${NC}"
    ISSUES=$((ISSUES + 1))
fi
echo ""

# 7. Check GitHub configuration
echo -e "${BOLD}7. GitHub Configuration Check...${NC}"

# Check SSH key
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo -e "   ${GREEN}✅ GitHub SSH authentication working${NC}"
else
    echo -e "   ${YELLOW}⚠️  GitHub SSH not configured or not accessible${NC}"
    echo -e "   ${YELLOW}Note: This is only needed if pushing to GitHub${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Check git config
GIT_USER=$(git config --global user.name 2>/dev/null)
GIT_EMAIL=$(git config --global user.email 2>/dev/null)

if [ ! -z "$GIT_USER" ] && [ ! -z "$GIT_EMAIL" ]; then
    echo -e "   ${GREEN}✅ Git configured: $GIT_USER <$GIT_EMAIL>${NC}"
else
    echo -e "   ${YELLOW}⚠️  Git user not fully configured${NC}"
    if [ -z "$GIT_USER" ]; then
        echo -e "   ${YELLOW}Fix: git config --global user.name \"Your Name\"${NC}"
    fi
    if [ -z "$GIT_EMAIL" ]; then
        echo -e "   ${YELLOW}Fix: git config --global user.email \"your@email.com\"${NC}"
    fi
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 8. Check system resources
echo -e "${BOLD}8. System Resources Check...${NC}"

# Check disk space
DISK_USAGE=$(df -h /home/wv3 | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt "80" ]; then
    echo -e "   ${GREEN}✅ Disk usage: ${DISK_USAGE}%${NC}"
elif [ "$DISK_USAGE" -lt "90" ]; then
    echo -e "   ${YELLOW}⚠️  Disk usage high: ${DISK_USAGE}%${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "   ${RED}❌ Disk critically full: ${DISK_USAGE}%${NC}"
    ISSUES=$((ISSUES + 1))
fi

# Check memory
MEM_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ "$MEM_USAGE" -lt "80" ]; then
    echo -e "   ${GREEN}✅ Memory usage: ${MEM_USAGE}%${NC}"
elif [ "$MEM_USAGE" -lt "90" ]; then
    echo -e "   ${YELLOW}⚠️  Memory usage high: ${MEM_USAGE}%${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "   ${RED}❌ Memory critically high: ${MEM_USAGE}%${NC}"
    ISSUES=$((ISSUES + 1))
fi

# Check load average
LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
CPU_COUNT=$(nproc)
LOAD_THRESHOLD=$(echo "$CPU_COUNT * 2" | bc)

if (( $(echo "$LOAD_AVG < $LOAD_THRESHOLD" | bc -l) )); then
    echo -e "   ${GREEN}✅ Load average: $LOAD_AVG (CPUs: $CPU_COUNT)${NC}"
else
    echo -e "   ${YELLOW}⚠️  Load average high: $LOAD_AVG (CPUs: $CPU_COUNT)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 9. Check template availability
echo -e "${BOLD}9. Template System Check...${NC}"
TEMPLATE_DIR="/home/wv3/ideabrow-pipeline/templates"
if [ -d "$TEMPLATE_DIR" ]; then
    TEMPLATE_COUNT=$(ls -1 $TEMPLATE_DIR 2>/dev/null | wc -l)
    if [ "$TEMPLATE_COUNT" -gt "0" ]; then
        echo -e "   ${GREEN}✅ Found $TEMPLATE_COUNT templates${NC}"
        
        # Check for template selector
        if [ -f "/home/wv3/ideabrow-pipeline/orchestrator/select_template.py" ]; then
            echo -e "   ${GREEN}✅ Template selector present${NC}"
        else
            echo -e "   ${YELLOW}⚠️  Template selector missing${NC}"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        echo -e "   ${YELLOW}⚠️  No templates found${NC}"
        echo -e "   ${YELLOW}Note: Templates are optional but recommended${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
fi
echo ""

# 10. Quick connectivity test
echo -e "${BOLD}10. Network Connectivity Check...${NC}"
if ping -c 1 github.com > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Can reach github.com${NC}"
else
    echo -e "   ${RED}❌ Cannot reach github.com${NC}"
    echo -e "   ${YELLOW}Check your network connection${NC}"
    ISSUES=$((ISSUES + 1))
fi

if curl -s https://api.github.com > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ GitHub API accessible${NC}"
else
    echo -e "   ${YELLOW}⚠️  GitHub API not accessible${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Summary
echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
if [ "$ISSUES" -eq "0" ] && [ "$WARNINGS" -eq "0" ]; then
    echo -e "${GREEN}${BOLD}✅ SYSTEM PERFECT - All checks passed!${NC}"
    echo ""
    echo -e "${GREEN}The IdeaBrow Pipeline is fully operational.${NC}"
    echo ""
    echo -e "${CYAN}Quick Start:${NC}"
    echo -e "  1. Monitor system: ${BOLD}python3 /home/wv3/ideabrow-pipeline/monitoring/pipeline_monitor.py${NC}"
    echo -e "  2. Watch mode: ${BOLD}python3 /home/wv3/ideabrow-pipeline/monitoring/pipeline_monitor.py -w${NC}"
    echo -e "  3. Project status: ${BOLD}/home/wv3/ideabrow-pipeline/monitoring/project_status.sh${NC}"
elif [ "$ISSUES" -eq "0" ]; then
    echo -e "${YELLOW}${BOLD}⚠️  SYSTEM READY - $WARNINGS warnings detected${NC}"
    echo ""
    echo -e "${GREEN}The system is operational but has some minor issues.${NC}"
    echo -e "${YELLOW}Review the warnings above for optimization opportunities.${NC}"
else
    echo -e "${RED}${BOLD}❌ ISSUES DETECTED - $ISSUES critical issues, $WARNINGS warnings${NC}"
    echo ""
    echo -e "${RED}Please fix the critical issues above before running the pipeline.${NC}"
    echo -e "${YELLOW}After fixing, run this health check again to verify.${NC}"
fi
echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Return exit code
exit $ISSUES