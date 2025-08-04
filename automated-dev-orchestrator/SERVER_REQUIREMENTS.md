# Server Implementation Requirements

## Current State
You have a working tmux script that:
- Creates named tmux sessions
- Opens 4 panes (Claude Code, terminal, ranger, other apps)
- Applies boilerplate templates from 300+ examples
- Requires human to manually trigger and configure

## Target State
Webhook-triggered system that automatically creates and manages development sessions without human intervention.

## Core Implementation Tasks

### 1. Build Webhook Receiver
**Technology**: Use Flask or FastAPI (pick whichever is already on the server)

**Endpoint**: `POST /create-session`

**Required functionality**:
```python
# Pseudocode
def create_session(webhook_data):
    validate_webhook(webhook_data)
    queue_job(webhook_data)
    return {"status": "queued", "session_name": f"{project_name}-dev"}
```

**Security**: 
- Validate webhook source (GitHub signature)
- Rate limiting
- Basic auth or token

### 2. Automate Tmux Session Creation

Transform your existing script to be parameter-driven:

**Current script (human-operated)**:
- Prompts for session name
- Prompts for template selection
- Opens interactive tmux

**New script (parameter-driven)**:
```bash
# create_dev_session.sh
SESSION_NAME=$1
REPO_URL=$2
TEMPLATE=$3
TRACKER_URL=$4

# No prompts, all automated
tmux new-session -d -s "$SESSION_NAME"
# ... rest of automation
```

**Key changes needed**:
- Remove all interactive prompts
- Accept parameters instead
- Run in detached mode (-d flag)
- Auto-select template based on hint
- Clone repo before starting

### 3. Context Injection for Claude Code

**Requirements**:
- Claude Code must start with PROGRESS_TRACKER.md loaded
- Working directory set to cloned repo
- Environment variables for API keys configured

**Implementation approach**:
```bash
# In tmux pane 1
tmux send-keys -t "$SESSION_NAME:0.0" "cd ~/projects/$PROJECT_NAME" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "claude-code PROGRESS_TRACKER.md" C-m
```

### 4. Template Selection Logic

**Simple matching**:
```python
def select_template(requirements_summary, template_hint):
    # First try exact hint match
    if template_hint and exists(f"templates/{template_hint}"):
        return template_hint
    
    # Fallback to keyword matching
    keywords = extract_keywords(requirements_summary)
    if "react" in keywords:
        return "react-typescript"
    elif "python" in keywords and "api" in keywords:
        return "python-fastapi"
    # ... more rules
    
    return "generic-starter"
```

## Success Criteria

### Minimum Viable Implementation
1. ✅ Webhook receives POST request and creates tmux session
2. ✅ Session has correct name and layout
3. ✅ Repository is cloned successfully
4. ✅ Claude Code starts with context file
5. ✅ No human intervention required

### Testing Checklist
```bash
# Test webhook
curl -X POST http://localhost:8080/create-session \
  -H "Content-Type: application/json" \
  -d '{"project_name": "test-app", "repo_url": "..."}'

# Verify session created
tmux ls | grep "test-app-dev"

# Attach and verify layout
tmux attach -t test-app-dev
```

## Implementation Order

### Phase 1: Basic Webhook (Day 1)
- Set up Flask/FastAPI server
- Create `/create-session` endpoint
- Test with curl

### Phase 2: Script Automation (Day 1-2)
- Modify existing tmux script
- Remove interactive elements
- Test with hardcoded values

### Phase 3: Integration (Day 2)
- Connect webhook to script
- Add repo cloning
- Test end-to-end

### Phase 4: Claude Code Context (Day 3)
- Add PROGRESS_TRACKER.md loading
- Configure environment
- Test autonomous operation

## Important Notes

**Keep it simple**:
- Don't build a queue system yet (process synchronously)
- Don't add database (use filesystem for state if needed)
- Don't over-engineer template matching (simple rules fine)
- Don't add monitoring yet (logs are enough)

**File Structure**:
```
~/dev-orchestrator/
├── server.py           # Webhook receiver
├── create_session.sh   # Modified tmux script
├── templates/          # Your existing 300+ templates
└── logs/              # Simple file logging
```

**Dependencies to install**:
```bash
pip install flask  # or fastapi
pip install requests
# tmux already installed
# claude-code already configured
```

## Example Webhook Handler

```python
from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/create-session', methods=['POST'])
def create_session():
    data = request.json
    
    # Extract required fields
    project_name = data['project_name']
    repo_url = data['repo_url']
    template_hint = data.get('template_hint', 'generic')
    
    # Call your tmux script
    cmd = [
        './create_session.sh',
        project_name,
        repo_url,
        template_hint
    ]
    
    try:
        subprocess.run(cmd, check=True)
        return jsonify({
            'status': 'success',
            'session': f'{project_name}-dev',
            'attach_command': f'tmux attach -t {project_name}-dev'
        })
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

Start here. Get this working. Then iterate.