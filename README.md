# IdeaBrow Automation Pipeline 🚀

**Transform project ideas into fully-developed applications automatically!**

## 🎯 Overview

The IdeaBrow Pipeline is a bulletproof automation system that:
- Takes app documentation from GitHub
- Creates development environment automatically  
- Builds complete applications using AI agent swarms
- Delivers working code in ~2 hours

## 🚀 Quick Start

### Start the Pipeline
```bash
cd /home/wv3/ideabrow-pipeline
./start_pipeline.sh
```

### Monitor Active Projects
```bash
# Real-time dashboard
python3 monitoring/pipeline_monitor.py

# Watch mode (auto-refresh)
python3 monitoring/pipeline_monitor.py -w

# Quick status check
monitoring/quick_status.sh
```

### Stop the Pipeline
```bash
./stop_pipeline.sh
```

## 📁 Directory Structure

```
ideabrow-pipeline/
├── github-workflow/          # GitHub Actions with deduplication
├── webhook-server/           # Enhanced webhook handler
├── orchestrator/             # Session creation & messaging
├── templates/                # Project templates
├── monitoring/               # CLI monitoring tools
├── start_pipeline.sh         # Main startup script
├── stop_pipeline.sh          # Shutdown script
└── README.md                # This file
```

## 🔄 How It Works

### 1. Input Phase
- Push app docs to `ideabrow-automation` repo
- GitHub Actions processes docs (with deduplication)
- Creates unique GitHub repo for project
- Sends webhook to start development

### 2. Development Phase  
- Webhook server creates tmux session with Claude Code
- AI follows 5-phase development process:
  - **Phase 1**: Template analysis (30 min)
  - **Phase 2**: Core features (30 min) 
  - **Phase 3**: Enhanced features (30 min)
  - **Phase 4**: Testing & polish (20 min)
  - **Phase 5**: Final review & auto-push (15 min)

### 3. Output Phase
- Complete application built locally
- Automatically pushed to GitHub
- Ready for review and deployment

## ✨ Key Features

### Deduplication & Reliability
- ✅ One docs push = exactly one project
- ✅ No duplicate webhooks or sessions
- ✅ Persistent phase scheduling (survives restarts)
- ✅ State tracking prevents processing same project twice

### Monitoring & Observability
- ✅ Real-time CLI dashboard
- ✅ Phase progression tracking
- ✅ Error detection and alerts
- ✅ System health monitoring
- ✅ Project session management

### Automation & AI
- ✅ Full AI agent swarm coordination
- ✅ Template-aware development
- ✅ Automatic git commits and pushes
- ✅ Quality assurance and testing
- ✅ Complete documentation generation

## 🛠 Configuration

### Webhook URL
Set this URL in your GitHub Actions workflow:
```
http://your-domain:8090/webhook
```

### Templates
Templates are located in `templates/` directory:
- `modern-saas/` - Full-stack SaaS templates with auth
- `clerk-auth/` - Clerk authentication templates

### Monitoring
All monitoring tools in `monitoring/` directory:
- `pipeline_monitor.py` - Main dashboard
- `phase_tracker.py` - Real-time phase tracking  
- `health_check.sh` - System health verification
- `cleanup_phases.sh` - Cleanup orphaned processes

## 🔧 Troubleshooting

### Check System Health
```bash
monitoring/health_check.sh
```

### View Active Projects
```bash
python3 monitoring/pipeline_monitor.py
```

### Check Webhook Logs
```bash
tmux attach -t ideabrow-pipeline
```

### Clean Up Orphaned Processes
```bash
monitoring/cleanup_phases.sh
```

### Manual Session Management
```bash
# List all sessions
orchestrator/session-utils.sh list

# Attach to latest project
orchestrator/session-utils.sh latest myproject

# Cleanup old sessions  
orchestrator/session-utils.sh cleanup
```

## 📊 Monitoring Commands

```bash
# Main monitoring dashboard
python3 monitoring/pipeline_monitor.py

# Watch mode (auto-refresh every 5s)
python3 monitoring/pipeline_monitor.py -w

# Real-time phase tracking
python3 monitoring/phase_tracker.py  

# Quick one-line status
monitoring/quick_status.sh

# Detailed project info
monitoring/project_status.sh myproject

# System health check
monitoring/health_check.sh
```

## 🎛 Admin Operations

### State Management
```bash
# View processed requests
curl http://localhost:8090/admin/state

# Cleanup old state (7+ days)
curl -X POST http://localhost:8090/admin/cleanup
```

### Manual Cleanup
```bash
# Stop old webhook servers
pkill -f webhook_server.py

# Clean scheduled phases
pkill -f "sleep.*send-claude-message"

# Remove orphaned tmux sessions
tmux kill-server  # CAREFUL: kills all sessions
```

## 🚨 Important Notes

- **One webhook per project**: Deduplication prevents duplicate processing
- **Auto-push enabled**: Phase 5 automatically pushes code to GitHub
- **Session persistence**: tmux sessions survive system reboots
- **State tracking**: All requests and cooldowns are persisted
- **Error recovery**: Graceful handling of failures without orphans

## 🏆 Success Criteria

✅ Push docs once → Creates exactly one repo  
✅ No duplicate webhooks or sessions  
✅ Code automatically pushed at completion  
✅ Clear monitoring of all active projects  
✅ Can handle multiple projects in parallel  
✅ Graceful error handling without orphans  

---

**The IdeaBrow Pipeline**: Your personal software factory. Input ideas, output applications.