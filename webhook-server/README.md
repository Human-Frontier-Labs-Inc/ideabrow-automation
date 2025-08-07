# Enhanced Webhook Server

An improved webhook server extracted from tmux-automation with deduplication, state management, and cooldown protection.

## Features

### Core Improvements
- **Request Deduplication**: Prevents processing same webhook twice using SHA-256 hashes
- **State Management**: Persistent tracking of processed requests and project cooldowns  
- **5-Minute Cooldown**: Rejects webhooks for projects created in last 5 minutes
- **Full Timestamp Support**: No truncation of project names with timestamps
- **Enhanced Error Handling**: Better logging and error responses
- **Admin Endpoints**: State inspection and cleanup capabilities

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

## Setup

1. **Virtual Environment** (already created):
   ```bash
   cd /home/wv3/ideabrow-pipeline
   python3 -m venv venv
   source venv/bin/activate
   pip install flask requests
   ```

2. **Start Server**:
   ```bash
   cd /home/wv3/ideabrow-pipeline/webhook-server
   ./start_server.sh
   ```

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
- `WEBHOOK_PORT` - Server port (default: 8090)

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
curl http://localhost:8090/health
```

View state statistics:  
```bash
curl http://localhost:8090/admin/state
```

Monitor logs:
```bash
tail -f /home/wv3/ideabrow-pipeline/webhook-server/logs/webhook.log
```