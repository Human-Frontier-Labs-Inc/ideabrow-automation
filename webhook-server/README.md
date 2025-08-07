# Enhanced Webhook Server

Production-ready webhook server for ideabrow-automation pipeline with deduplication, state management, and intelligent template selection.

## Features

### Core Improvements
- **Request Deduplication**: Prevents processing same webhook twice using SHA-256 hashes
- **State Management**: Persistent tracking of processed requests and project cooldowns  
- **5-Minute Cooldown**: Rejects webhooks for projects created in last 5 minutes
- **Full Timestamp Support**: No truncation of project names with timestamps
- **Enhanced Error Handling**: Better logging and error responses
- **Admin Endpoints**: State inspection and cleanup capabilities
- **Template Selection**: Intelligent selection from 41+ templates (always uses Clerk auth)

### Phase Scheduler Integration
- Maintains nohup-based phase scheduling for persistence
- 5-phase automated development workflow
- Agent swarm coordination messaging

### Webhook Adapter
- Transform ideabrow-automation webhooks
- Fetch GitHub content (PROGRESS_TRACKER.md)
- Generate intelligent starter prompts
- SSH URL conversion for Git cloning

## Directory Structure

```
webhook-server/
├── webhook_server.py      # Main enhanced server
├── phase_scheduler.py     # Phase management with nohup fix
├── webhook_adapter.py     # Payload transformation
├── start_server.sh        # Startup script
├── requirements.txt       # Python dependencies  
├── logs/                  # Server logs
└── state/                 # State files
    ├── processed_requests.json
    └── project_cooldowns.json
```

## Deployment

### Quick Start
```bash
# Start webhook server on port 5000
cd /home/wv3/ideabrow-automation/webhook-server
nohup python3 webhook_server.py > webhook_server.log 2>&1 &

# Create cloudflared tunnel for GitHub webhook
cloudflared tunnel --url http://localhost:5000

# Update GitHub secret with tunnel URL (copy URL from cloudflared output)
gh secret set DEV_SERVER_WEBHOOK_URL --body "https://your-url.trycloudflare.com" \
  --repo Human-Frontier-Labs-Inc/ideabrow-automation
```

### Port Configuration
- **Default Port**: 5000
- **Alternative Ports**: 5001-5010 (for multiple instances)
- **Set custom port**: `PORT=5001 python3 webhook_server.py`

## API Endpoints

### Main Endpoints
- `POST /webhook` - Main webhook endpoint
- `POST /webhook/<token>` - Webhook with token
- `POST /` - Alternative webhook endpoint
- `GET /health` - Health check with state info

### Status & Testing
- `GET /status/<project_name>` - Project status with cooldown info
- `POST /test` - Test endpoint for manual testing

### Admin Endpoints
- `GET /admin/state` - View current state statistics
- `POST /admin/cleanup` - Clean up old state entries

## State Management

### Request Deduplication
- Uses SHA-256 hash of `project_name:timestamp`
- Stored in `state/processed_requests.json`
- Returns 409 status for duplicate requests

### Project Cooldown
- 5-minute cooldown after project creation
- Stored in `state/project_cooldowns.json` 
- Returns 429 status during cooldown period
- Admin can view active cooldowns via `/admin/state`

### Automatic Cleanup
- Cleans entries older than 7 days on startup
- Manual cleanup via `/admin/cleanup` endpoint
- Configurable retention period

## Configuration

Environment variables:
- `PORT` - Server port (default: 5000)
- `WEBHOOK_PORT` - Alternative port variable (default: 5000)

Internal settings in `webhook_server.py`:
- `COOLDOWN_MINUTES` - Cooldown period (default: 5)
- `SCRIPTS_DIR` - Path to tmux automation scripts
- `STATE_DIR` - State file directory

## Enhanced Features

### Project Name Handling
- Preserves full timestamps (no 30-character truncation)
- Consistent cleaning and validation
- Safe for tmux session names

### Error Handling
- Comprehensive logging to `logs/webhook.log`
- Request ID tracking for debugging
- Graceful fallbacks for missing dependencies

### Phase Scheduling
- nohup-based persistence across process exits
- 5-phase automated workflow
- Agent swarm coordination prompts

## Dependencies

- **Flask 3.1.1** - Web framework
- **Requests 2.32.4** - HTTP library for GitHub API calls
- **tmux-automation scripts** - Template selection and session creation
- **Claude orchestrator** - Phase scheduling integration

## Integration

Works with:
- ideabrow-automation webhooks (auto-transforms payload)
- tmux session creation scripts
- Claude Code orchestrator system
- Phase-based development workflow

## Monitoring

Check server health:
```bash
curl http://localhost:5000/health
```

View state statistics:  
```bash
curl http://localhost:5000/admin/state
```

Monitor logs:
```bash
tail -f /home/wv3/ideabrow-automation/webhook-server/logs/webhook.log
```

Check running process:
```bash
ps aux | grep webhook_server
```

View created tmux sessions:
```bash
tmux ls | grep "2025-"
```