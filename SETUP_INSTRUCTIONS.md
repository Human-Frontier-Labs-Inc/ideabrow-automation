# Setup Instructions for IdeaBrow Automation

## GitHub Secrets Configuration

To fully enable this automation pipeline, configure these secrets in your GitHub repository:

### Required Secrets

1. **WEBHOOK_URL** (Required for automation)
   - Your webhook server endpoint
   - Example: `https://webhook.yourdomain.com/webhook`
   - Without this, docs will be processed but no development will start

2. **PAT_TOKEN** (Optional but recommended)
   - Personal Access Token with `repo` scope
   - Allows automatic creation of new repositories
   - Without this, webhook will still fire but repo won't be created
   - To create: GitHub Settings → Developer settings → Personal access tokens → Generate new token

## How It Works

### With Both Secrets Configured
1. Push docs to `/docs` folder
2. GitHub Actions processes docs
3. Creates new private repository
4. Sends webhook to your server
5. Server spawns tmux session with AI
6. AI builds the application
7. Code auto-pushed to new repo

### With Only WEBHOOK_URL
1. Push docs to `/docs` folder
2. GitHub Actions processes docs
3. Sends webhook with placeholder repo URL
4. Server spawns tmux session
5. AI builds locally (you create repo manually later)

### With No Secrets
1. Push docs to `/docs` folder
2. Docs get archived in `/processed`
3. No automation triggered (manual processing needed)

## Local Webhook Server Setup

On your development server:

```bash
# Start webhook server
cd webhook-server
source ../venv/bin/activate
python webhook_server.py

# Or use the start script
./start_server.sh
```

## Testing the Pipeline

1. Create test docs:
```bash
echo "# My Amazing App" > docs/document-1.md
echo "Build a todo list with AI" >> docs/document-1.md
```

2. Push to GitHub:
```bash
git add docs/
git commit -m "New project: My Amazing App"
git push
```

3. Watch the magic happen!

## Monitoring

```bash
# View active projects
python monitoring/pipeline_monitor.py

# Check webhook logs
tail -f webhook-server/logs/webhook.log

# Attach to a session
tmux attach -t project-name-timestamp
```

## Troubleshooting

### Webhook Not Firing
- Check WEBHOOK_URL secret is set correctly
- Ensure webhook server is running and accessible
- Check GitHub Actions logs for errors

### Repository Not Created
- Add PAT_TOKEN secret with repo permissions
- Or manually create repos and update webhook payload

### Duplicate Projects
- System has built-in deduplication
- 5-minute cooldown prevents rapid re-triggers
- Check `webhook-server/state/` for tracking files

## Security Notes

- Keep WEBHOOK_URL private
- Use HTTPS for webhook endpoint
- PAT_TOKEN should have minimal required permissions
- Webhook server validates and sanitizes all inputs