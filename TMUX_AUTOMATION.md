# Tmux Automation Integration

## What It Does
When this workflow creates a GitHub repository, it triggers a webhook that automatically creates a development environment with:
- Tmux session with 4 panes (Claude Code, Ranger, Terminal, Monitor)
- Selected template files based on project requirements
- Starter prompt injected into Claude Code
- GitHub repo cloned with docs and PROGRESS_TRACKER.md

## How It Works
1. Workflow processes docs → creates GitHub repo → sends webhook
2. Webhook server (port 8090) receives payload with repo info
3. LLM selects appropriate template from 83 available
4. Script clones GitHub repo and adds template files
5. Tmux session created with everything ready

## Current Setup
- Webhook URL: Set as GitHub secret (currently using quick tunnel)
- No authentication (testing only)
- Creates sessions in /home/wv3/projects/

## Files
- `/home/wv3/tmux-automation/` - Main automation system
- `server/webhook_server.py` - Flask webhook receiver
- `scripts/select_template.py` - LLM template selection
- `scripts/create_automated_session.sh` - Tmux session creator