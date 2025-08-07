#!/bin/bash
# Quick Pipeline Tester - All-in-one testing script
# Usage: ./quick_test.sh [component|flow|reset]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

show_usage() {
    echo "Usage: ./quick_test.sh [component|flow|reset]"
    echo ""
    echo "component - Test individual components"
    echo "flow      - Test complete end-to-end flow"  
    echo "reset     - Clean up all test data"
}

test_components() {
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║        COMPONENT TESTING               ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${YELLOW}1. Testing docs processing...${NC}"
    python3 test_pipeline.py docs || exit 1
    echo ""
    
    echo -e "${YELLOW}2. Testing webhook server...${NC}"
    if ! curl -s http://localhost:8090/health | grep -q "healthy"; then
        echo -e "${RED}❌ Webhook server not running!${NC}"
        echo "Start it with: ../start_pipeline.sh"
        exit 1
    fi
    echo -e "${GREEN}✅ Webhook server is healthy${NC}"
    echo ""
    
    echo -e "${YELLOW}3. Testing GitHub workflow mock...${NC}"
    python3 mock_github.py setup
    python3 mock_github.py process
    echo ""
    
    echo -e "${GREEN}✅ All components working!${NC}"
}

test_flow() {
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║        END-TO-END FLOW TEST            ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""
    
    # Check webhook server
    if ! curl -s http://localhost:8090/health | grep -q "healthy"; then
        echo -e "${RED}❌ Webhook server not running!${NC}"
        echo "Start it with: ../start_pipeline.sh"
        exit 1
    fi
    
    echo -e "${YELLOW}Running full pipeline test...${NC}"
    python3 test_pipeline.py full || exit 1
    echo ""
    
    echo -e "${GREEN}✅ End-to-end test complete!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "• Monitor: python3 ../monitoring/pipeline_monitor.py"
    echo "• View sessions: tmux list-sessions"
    echo "• Check specific project: tmux attach -t <project-name>"
}

reset_tests() {
    echo -e "${YELLOW}🧹 Cleaning up test data...${NC}"
    
    # Clean mock GitHub data
    python3 mock_github.py cleanup
    
    # Clean any test tmux sessions
    for session in $(tmux list-sessions -F "#{session_name}" 2>/dev/null | grep "test-app" || true); do
        echo "Killing test session: $session"
        tmux kill-session -t "$session" 2>/dev/null || true
    done
    
    echo -e "${GREEN}✅ Test data cleaned up${NC}"
}

main() {
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi
    
    case "$1" in
        component)
            test_components
            ;;
        flow)
            test_flow
            ;;
        reset)
            reset_tests
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"