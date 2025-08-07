# Deployment Registry

## Active Services

### 1. Webhook Server (ideabrow-automation)
- **Service**: webhook_server.py
- **Port**: 5000
- **Method**: nohup + cloudflared tunnel
- **Location**: `/home/wv3/ideabrow-automation/webhook-server/`
- **Process**: Running as background process with nohup
- **Tunnel**: Cloudflared (auto-generated URL, expires after ~3 days)
- **Purpose**: Receives webhooks from GitHub Actions, creates tmux dev sessions
- **Start Command**: 
  ```bash
  cd /home/wv3/ideabrow-automation/webhook-server
  nohup python3 webhook_server.py > webhook_server.log 2>&1 &
  cloudflared tunnel --url http://localhost:5000
  ```
- **Dependencies**: Flask, tmux, cloudflared
- **State Files**: 
  - `webhook_state.json` - Request deduplication
  - `logs/webhook.log` - Activity logs

### 2. Ideabrow Pipeline Webhook (backup)
- **Service**: webhook_server.py (pipeline version)
- **Port**: 5001 (if needed as backup)
- **Method**: nohup + cloudflared tunnel
- **Location**: `/home/wv3/ideabrow-pipeline/webhook-server/`
- **Purpose**: Backup/testing webhook server
- **Start Command**:
  ```bash
  cd /home/wv3/ideabrow-pipeline/webhook-server
  PORT=5001 nohup python3 webhook_server.py > webhook_server.log 2>&1 &
  cloudflared tunnel --url http://localhost:5001
  ```

## Port Allocation Strategy

| Port | Service | Status |
|------|---------|--------|
| 5000 | Main webhook server | Active |
| 5001 | Backup webhook server | Available |
| 5002-5010 | Reserved for future webhooks | Available |
| 8000-8010 | Reserved for app deployments | Available |
| 3000-3010 | Reserved for Next.js dev servers | Available |

## Deployment Methods

### 1. Cloudflared Tunnel (Current)
**Pros:**
- No port forwarding needed
- Automatic HTTPS
- Works behind NAT/firewall
- Quick setup

**Cons:**
- URLs expire after ~3 days
- Requires cloudflared binary
- Not suitable for production

**Usage:**
```bash
cloudflared tunnel --url http://localhost:PORT
```

### 2. Systemd Service (Production Ready)
**Template:** See `/home/wv3/ideabrow-automation/deployment/webhook.service`

**Deploy:**
```bash
sudo cp webhook.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable webhook
sudo systemctl start webhook
```

### 3. Docker Container (Future)
**Dockerfile:** See `/home/wv3/ideabrow-automation/Dockerfile`

**Deploy:**
```bash
docker build -t ideabrow-webhook .
docker run -d -p 5000:5000 --name webhook ideabrow-webhook
```

## Critical URLs & Secrets

### GitHub Secrets Required
- `DEV_SERVER_WEBHOOK_URL`: Cloudflared tunnel URL (update every 3 days)
- `GH_PAT`: GitHub Personal Access Token for repo creation
- `OPENROUTER_API_KEY`: For AI progress tracker generation

### Update Webhook URL
```bash
# 1. Get new tunnel URL
cloudflared tunnel --url http://localhost:5000

# 2. Update GitHub secret
gh secret set DEV_SERVER_WEBHOOK_URL --body "https://your-new-url.trycloudflare.com" \
  --repo Human-Frontier-Labs-Inc/ideabrow-automation
```

## Monitoring

### Check Service Status
```bash
# Check if webhook server is running
ps aux | grep webhook_server

# Check recent logs
tail -f /home/wv3/ideabrow-automation/webhook-server/logs/webhook.log

# Check tmux sessions created
tmux ls | grep "2025-"

# Check port usage
lsof -i :5000
```

### Health Check Endpoint
```bash
curl http://localhost:5000/health
```

## Troubleshooting

### Service Not Responding
1. Check process: `ps aux | grep webhook_server`
2. Check logs: `tail -100 webhook_server.log`
3. Restart service:
   ```bash
   pkill -f webhook_server.py
   cd /home/wv3/ideabrow-automation/webhook-server
   nohup python3 webhook_server.py > webhook_server.log 2>&1 &
   ```

### Cloudflared Tunnel Expired
1. Kill old tunnel: `pkill cloudflared`
2. Start new tunnel: `cloudflared tunnel --url http://localhost:5000`
3. Update GitHub secret with new URL

### Port Already in Use
```bash
# Find process using port
lsof -i :5000
# Kill process
kill -9 <PID>
```

## Security Notes

- Webhook server validates request signatures (when implemented)
- Runs as non-root user
- No direct internet exposure (through cloudflared)
- Request deduplication prevents replay attacks
- 5-minute cooldown for duplicate requests

## Last Updated
- Date: 2025-08-07
- Version: 1.0.0
- Maintained by: ideabrow-automation system