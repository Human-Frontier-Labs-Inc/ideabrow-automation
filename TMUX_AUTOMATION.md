# Tmux Automation Integration

## What It Does
When this workflow creates a GitHub repository, it triggers a webhook that automatically creates a development environment with:
- Tmux session with 4 panes (Claude Code, Ranger, Terminal, Monitor)
- Selected template files based on project requirements
- Starter prompt injected into Claude Code
- GitHub repo cloned with docs and PROGRESS_TRACKER.md
- AI-generated progress tracker with proper project naming

## How It Works
1. Workflow processes docs → generates AI tracker → creates GitHub repo → sends webhook
2. Webhook server (port 5000) receives payload with repo info
3. Enhanced template selector chooses from 41+ available templates (always Clerk auth)
4. Script clones GitHub repo and adds template files
5. Tmux session created with everything ready
6. 5-phase development workflow scheduled with nohup persistence

## Deployment Configuration

### Primary Webhook Server
- **Location**: `/home/wv3/ideabrow-automation/webhook-server/`
- **Port**: 5000 (default)
- **Method**: nohup + cloudflared tunnel
- **Start Command**:
  ```bash
  cd /home/wv3/ideabrow-automation/webhook-server
  nohup python3 webhook_server.py > webhook_server.log 2>&1 &
  cloudflared tunnel --url http://localhost:5000
  ```

### GitHub Webhook Setup
- **Secret Name**: `DEV_SERVER_WEBHOOK_URL`
- **Update Command**:
  ```bash
  gh secret set DEV_SERVER_WEBHOOK_URL --body "https://your-url.trycloudflare.com" \
    --repo Human-Frontier-Labs-Inc/ideabrow-automation
  ```
- **Note**: Cloudflared URLs expire after ~3 days, requires periodic update

### Port Allocation
- 5000: Main webhook server (ideabrow-automation)
- 5001-5010: Reserved for additional webhook instances
- 8000-8010: Reserved for app deployments
- 3000-3010: Reserved for Next.js dev servers

## Template Selection
- **Total Templates**: 41+ (from multiple categories)
- **Categories**: modern-saas, clerk-auth, full-stack, social-media, crm-dashboards, realtime
- **Authentication**: Always uses Clerk (never NextAuth)
- **Selection Method**: Intelligent scoring based on requirements
- **Enhanced Selector**: `webhook-server/select_template_enhanced.py`

## Files
- `/home/wv3/ideabrow-automation/webhook-server/` - Enhanced webhook server
- `webhook_server.py` - Main Flask server (port 5000)
- `select_template_enhanced.py` - 41+ template selector
- `webhook_adapter.py` - Payload transformation
- `phase_scheduler.py` - 5-phase development scheduling
- `.claude/agent_comms/DEPLOYMENT_REGISTRY.md` - Complete deployment documentation