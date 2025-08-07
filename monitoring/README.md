# IdeaBrow Pipeline - CLI Monitoring System

A comprehensive set of CLI tools for monitoring and managing the IdeaBrow pipeline system.

## 🚀 Quick Start

### Main Dashboard
```bash
# Full monitoring dashboard
python3 pipeline_monitor.py

# Watch mode (auto-refresh every 5 seconds)
python3 pipeline_monitor.py -w

# JSON output for integration
python3 pipeline_monitor.py --json
```

### Quick Status
```bash
# One-line summary
./quick_status.sh

# Specific info
./quick_status.sh projects  # List active projects
./quick_status.sh phases    # Show scheduled phases
./quick_status.sh health    # System health
./quick_status.sh webhook   # Webhook status
./quick_status.sh full      # All information
```

## 📊 Monitoring Tools

### 1. **pipeline_monitor.py** - Main Dashboard
The primary monitoring tool with comprehensive status display.

**Features:**
- Active projects with current phase
- Scheduled phases timeline
- Webhook server status
- Duplicate detection
- System health metrics
- Color-coded status indicators

**Usage:**
```bash
python3 pipeline_monitor.py          # Single run
python3 pipeline_monitor.py -w       # Watch mode
python3 pipeline_monitor.py -w -i 10 # Custom interval (10 seconds)
python3 pipeline_monitor.py --json   # JSON output
```

### 2. **phase_tracker.py** - Real-time Phase Tracking
Live monitoring of phase execution across all projects.

**Features:**
- Real-time phase progression
- Progress bars for each project
- Phase completion notifications
- Upcoming phase schedule
- Animated status indicators

**Usage:**
```bash
python3 phase_tracker.py           # Default 2-second refresh
python3 phase_tracker.py -i 5      # 5-second refresh
python3 phase_tracker.py -a        # Show tmux activity
python3 phase_tracker.py --once    # Run once and exit
```

### 3. **project_status.sh** - Detailed Project View
In-depth information about specific projects.

**Features:**
- Project session status
- Phase progress details
- Recent activity from tmux
- Webhook logs for project
- State file information

**Usage:**
```bash
./project_status.sh              # List all projects
./project_status.sh myapp-v1     # Specific project details
./project_status.sh --help       # Help information
```

### 4. **health_check.sh** - System Diagnostics
Comprehensive health check of the entire pipeline system.

**Features:**
- Webhook server check
- Python environment validation
- Orchestrator scripts verification
- Directory structure check
- Resource usage monitoring
- Network connectivity test

**Usage:**
```bash
./health_check.sh     # Run full health check
```

### 5. **cleanup_phases.sh** - System Cleanup
Remove orphaned processes and clean up stale resources.

**Features:**
- Remove duplicate scheduled phases
- Clean orphaned sleep processes
- Remove stale tmux sessions
- Clean old state files
- Truncate large log files

**Usage:**
```bash
./cleanup_phases.sh           # Interactive cleanup
./cleanup_phases.sh --dry-run # Preview changes
./cleanup_phases.sh --force   # Force cleanup
./cleanup_phases.sh -v        # Verbose output
```

### 6. **quick_status.sh** - Instant Status
Quick one-liner status checks for scripts and automation.

**Usage:**
```bash
./quick_status.sh          # Summary line
./quick_status.sh p        # Projects
./quick_status.sh ph       # Phases
./quick_status.sh h        # Health
./quick_status.sh w        # Webhook
./quick_status.sh f        # Full status
```

## 🎨 Status Indicators

The monitoring tools use color-coded indicators:

- 🟢 **Green**: Healthy, running, completed
- 🟡 **Yellow**: Warning, in-progress, attention needed
- 🔴 **Red**: Error, stopped, critical issue
- 🔵 **Blue**: Information, neutral status
- 🟣 **Cyan**: System messages, timestamps

## 📈 Monitoring Workflow

### Daily Operations
1. Start with health check: `./health_check.sh`
2. Monitor dashboard: `python3 pipeline_monitor.py -w`
3. Track phases: `python3 phase_tracker.py`

### Troubleshooting
1. Check specific project: `./project_status.sh PROJECT_NAME`
2. Review system health: `./health_check.sh`
3. Clean up if needed: `./cleanup_phases.sh --dry-run`

### Quick Checks
```bash
# One-liner status in scripts
STATUS=$(./quick_status.sh)

# Check if webhook is running
if ./quick_status.sh w | grep -q "Running"; then
    echo "Webhook is up"
fi
```

## 🔧 Integration

### Aliases (add to ~/.bashrc)
```bash
alias ipmon='python3 /home/wv3/ideabrow-pipeline/monitoring/pipeline_monitor.py'
alias ipwatch='python3 /home/wv3/ideabrow-pipeline/monitoring/pipeline_monitor.py -w'
alias ipphases='python3 /home/wv3/ideabrow-pipeline/monitoring/phase_tracker.py'
alias ipstatus='/home/wv3/ideabrow-pipeline/monitoring/quick_status.sh'
alias iphealth='/home/wv3/ideabrow-pipeline/monitoring/health_check.sh'
alias ipclean='/home/wv3/ideabrow-pipeline/monitoring/cleanup_phases.sh'
```

### Cron Monitoring
```bash
# Add to crontab for regular cleanup
0 */6 * * * /home/wv3/ideabrow-pipeline/monitoring/cleanup_phases.sh --force

# Regular health check with notification
*/30 * * * * /home/wv3/ideabrow-pipeline/monitoring/health_check.sh || notify-send "Pipeline Issue"
```

### JSON Integration
```python
import subprocess
import json

# Get pipeline status as JSON
result = subprocess.run(
    ['python3', '/home/wv3/ideabrow-pipeline/monitoring/pipeline_monitor.py', '--json'],
    capture_output=True,
    text=True
)

status = json.loads(result.stdout)
print(f"Active projects: {len(status['projects'])}")
print(f"Health issues: {status['health']['issues']}")
```

## 🚨 Common Issues

### Webhook Server Not Running
```bash
cd /home/wv3/ideabrow-pipeline/webhook-server
./start_server.sh
```

### Duplicate Phases Detected
```bash
./cleanup_phases.sh --dry-run  # Preview
./cleanup_phases.sh --force    # Clean
```

### High Resource Usage
```bash
./health_check.sh              # Check resources
./cleanup_phases.sh --force    # Clean up
./project_status.sh            # Check active projects
```

## 📝 Notes

- All tools are non-destructive by default
- Use `--dry-run` to preview changes
- Watch modes can be stopped with Ctrl+C
- JSON output available for automation
- Color output automatically disabled when piped

## 🎯 Best Practices

1. **Regular Monitoring**: Keep `pipeline_monitor.py -w` running during active development
2. **Daily Cleanup**: Run `cleanup_phases.sh` daily to prevent resource buildup
3. **Health Checks**: Run `health_check.sh` before starting new projects
4. **Phase Tracking**: Use `phase_tracker.py` to monitor long-running projects
5. **Quick Status**: Use `quick_status.sh` in scripts for automation

## 📦 Requirements

- Python 3.6+
- tmux
- Standard Unix tools (ps, grep, awk, etc.)
- Write access to state/logs directories

## 🔗 Related Documentation

- Main Pipeline: `/home/wv3/ideabrow-pipeline/README.md`
- Webhook Server: `/home/wv3/ideabrow-pipeline/webhook-server/README.md`
- Orchestrator: `/home/wv3/ideabrow-pipeline/orchestrator/README.md`