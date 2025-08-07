#!/usr/bin/env python3
"""
IdeaBrow Pipeline Monitor - Comprehensive CLI monitoring for the entire pipeline
Tracks projects, phases, webhook processing, GitHub repos, and system health
"""

import subprocess
import json
import re
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import time

# ANSI color codes for CLI formatting
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DIM = '\033[2m'

class PipelineMonitor:
    def __init__(self):
        self.pipeline_dir = Path("/home/wv3/ideabrow-pipeline")
        self.state_dir = self.pipeline_dir / "webhook-server" / "state"
        self.logs_dir = self.pipeline_dir / "webhook-server" / "logs"
        self.orchestrator_path = self.pipeline_dir / "orchestrator"
        
    def get_active_projects(self) -> List[Dict]:
        """Get all active tmux sessions with their current status"""
        try:
            result = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name}"],
                capture_output=True,
                text=True
            )
            
            projects = []
            for session_name in result.stdout.strip().split('\n'):
                if session_name and session_name not in ['tmux-orc', 'server']:
                    project_info = self._get_project_details(session_name)
                    if project_info:
                        projects.append(project_info)
            
            return sorted(projects, key=lambda x: x.get('created', ''))
            
        except Exception as e:
            return []
    
    def _get_project_details(self, session_name: str) -> Optional[Dict]:
        """Get detailed information about a project"""
        try:
            # Check if Claude is running in this session
            pane_result = subprocess.run(
                ["tmux", "list-panes", "-t", f"{session_name}:0", "-F", "#{pane_current_command}"],
                capture_output=True,
                text=True,
                stderr=subprocess.DEVNULL
            )
            
            if 'claude' not in pane_result.stdout.lower():
                return None
            
            # Get state file info
            state_file = self.state_dir / f"{session_name}_state.json"
            tracker_file = self.state_dir / f"{session_name}_tracker.json"
            
            project_info = {
                'name': session_name,
                'status': 'active',
                'current_phase': 'Unknown',
                'created': 'Unknown',
                'repo_url': None,
                'errors': []
            }
            
            # Read state file
            if state_file.exists():
                try:
                    with open(state_file) as f:
                        data = json.load(f)
                        project_info['created'] = data.get('timestamp', 'Unknown')
                        project_info['repo_url'] = data.get('repo_url')
                except:
                    project_info['errors'].append('Invalid state file')
            
            # Read tracker file for current phase
            if tracker_file.exists():
                try:
                    with open(tracker_file) as f:
                        tracker = json.load(f)
                        # Find current phase
                        for phase in tracker.get('phases', []):
                            if phase.get('status') == 'in_progress':
                                project_info['current_phase'] = f"Phase {phase.get('phase_number', '?')}: {phase.get('name', 'Unknown')}"
                                break
                        else:
                            # Check for completed phases
                            completed = [p for p in tracker.get('phases', []) if p.get('status') == 'completed']
                            if completed:
                                last = completed[-1]
                                project_info['current_phase'] = f"Completed Phase {last.get('phase_number', '?')}"
                except:
                    project_info['errors'].append('Invalid tracker file')
            
            # Check for recent activity in pane
            capture_result = subprocess.run(
                ["tmux", "capture-pane", "-t", f"{session_name}:0", "-p", "-S", "-10"],
                capture_output=True,
                text=True,
                stderr=subprocess.DEVNULL
            )
            
            if capture_result.stdout:
                lines = capture_result.stdout.strip().split('\n')
                # Look for errors or important messages
                for line in lines[-5:]:
                    if 'error' in line.lower() or 'failed' in line.lower():
                        project_info['errors'].append(line.strip()[:80])
            
            return project_info
            
        except Exception as e:
            return None
    
    def get_scheduled_phases(self) -> List[Dict]:
        """Find all scheduled phase messages in the process list"""
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )
            
            scheduled = []
            for line in result.stdout.split('\n'):
                # Look for sleep processes with phase scheduling
                if 'sleep' in line and ('send-claude-message' in line or 'PHASE' in line):
                    # Extract details
                    match = re.search(r'sleep (\d+)', line)
                    if match:
                        sleep_seconds = int(match.group(1))
                        
                        # Extract project name
                        proj_match = re.search(r'(\S+):0(?:\.0)?', line)
                        project_name = proj_match.group(1) if proj_match else "Unknown"
                        
                        # Extract phase number
                        phase_match = re.search(r'PHASE (\d+)', line)
                        phase_num = phase_match.group(1) if phase_match else "?"
                        
                        # Extract PID
                        parts = line.split()
                        pid = parts[1]
                        
                        # Calculate when it will run
                        run_time = datetime.now() + timedelta(seconds=sleep_seconds)
                        
                        scheduled.append({
                            'pid': pid,
                            'project': project_name,
                            'phase': phase_num,
                            'run_time': run_time,
                            'minutes_from_now': sleep_seconds // 60
                        })
            
            return sorted(scheduled, key=lambda x: x['minutes_from_now'])
            
        except Exception as e:
            return []
    
    def get_webhook_status(self) -> Dict:
        """Check webhook server status and recent activity"""
        status = {
            'running': False,
            'port': 8091,
            'recent_webhooks': [],
            'errors': []
        }
        
        # Check if server is running
        result = subprocess.run(
            ["pgrep", "-f", "webhook_server.py"],
            capture_output=True
        )
        status['running'] = result.returncode == 0
        
        if status['running']:
            # Get PID and check port
            pid = result.stdout.decode().strip().split('\n')[0]
            port_check = subprocess.run(
                ["lsof", "-i", f":8090", "-t"],
                capture_output=True,
                text=True
            )
            if port_check.returncode != 0:
                status['errors'].append("Server running but port 8090 not bound")
        
        # Check recent webhook log
        webhook_log = self.logs_dir / "webhook.log"
        if webhook_log.exists():
            try:
                # Get last 100 lines
                result = subprocess.run(
                    ["tail", "-100", str(webhook_log)],
                    capture_output=True,
                    text=True
                )
                
                for line in result.stdout.split('\n'):
                    if 'Processing webhook' in line:
                        # Extract timestamp and repo
                        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                        repo_match = re.search(r'repo: (\S+)', line)
                        if timestamp_match and repo_match:
                            status['recent_webhooks'].append({
                                'time': timestamp_match.group(1),
                                'repo': repo_match.group(1)
                            })
                    elif 'ERROR' in line:
                        status['errors'].append(line.strip()[:100])
                
                # Keep only last 5 webhooks
                status['recent_webhooks'] = status['recent_webhooks'][-5:]
                
            except:
                pass
        
        return status
    
    def check_duplicates(self) -> List[str]:
        """Check for duplicate project sessions or scheduled phases"""
        duplicates = []
        
        # Check for duplicate scheduled phases
        scheduled = self.get_scheduled_phases()
        seen = {}
        for phase in scheduled:
            key = f"{phase['project']}-phase-{phase['phase']}"
            if key in seen:
                duplicates.append(f"Duplicate scheduled: {phase['project']} Phase {phase['phase']} (PIDs: {seen[key]}, {phase['pid']})")
            else:
                seen[key] = phase['pid']
        
        # Check for duplicate state files
        if self.state_dir.exists():
            projects = {}
            for state_file in self.state_dir.glob("*_state.json"):
                try:
                    with open(state_file) as f:
                        data = json.load(f)
                        repo = data.get('repo_url', '').split('/')[-1]
                        if repo and repo in projects:
                            duplicates.append(f"Duplicate repo: {repo} in {state_file.name} and {projects[repo]}")
                        elif repo:
                            projects[repo] = state_file.name
                except:
                    pass
        
        return duplicates
    
    def get_system_health(self) -> Dict:
        """Comprehensive system health check"""
        health = {
            'webhook_server': False,
            'orchestrator_scripts': False,
            'state_directory': False,
            'github_ssh': False,
            'disk_space': 0,
            'memory_usage': 0,
            'issues': []
        }
        
        # Check webhook server
        webhook_status = self.get_webhook_status()
        health['webhook_server'] = webhook_status['running']
        if not health['webhook_server']:
            health['issues'].append("Webhook server not running")
        
        # Check orchestrator scripts
        required_scripts = [
            "send-claude-message.sh",
            "schedule_with_note.sh",
            "create_automated_session.sh"
        ]
        
        all_present = True
        for script in required_scripts:
            script_path = self.orchestrator_path / script
            if not script_path.exists() or not os.access(script_path, os.X_OK):
                all_present = False
                health['issues'].append(f"Missing or non-executable: {script}")
        
        health['orchestrator_scripts'] = all_present
        
        # Check state directory
        health['state_directory'] = self.state_dir.exists()
        if not health['state_directory']:
            health['issues'].append("State directory missing")
        
        # Check GitHub SSH
        result = subprocess.run(
            ["ssh", "-T", "git@github.com"],
            capture_output=True,
            text=True,
            timeout=5
        )
        health['github_ssh'] = "successfully authenticated" in result.stderr
        
        # Check disk space
        try:
            result = subprocess.run(
                ["df", "-h", str(self.pipeline_dir)],
                capture_output=True,
                text=True
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 5:
                    usage = parts[4].rstrip('%')
                    health['disk_space'] = int(usage)
                    if health['disk_space'] > 90:
                        health['issues'].append(f"Low disk space: {usage}% used")
        except:
            pass
        
        # Check memory usage
        try:
            result = subprocess.run(
                ["free", "-m"],
                capture_output=True,
                text=True
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 3:
                    total = int(parts[1])
                    used = int(parts[2])
                    health['memory_usage'] = int((used / total) * 100)
                    if health['memory_usage'] > 90:
                        health['issues'].append(f"High memory usage: {health['memory_usage']}%")
        except:
            pass
        
        return health
    
    def display_status(self, watch_mode=False):
        """Display comprehensive status dashboard"""
        if watch_mode:
            os.system('clear')
        
        # Header
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}              IDEABROW PIPELINE - CLI MONITORING DASHBOARD{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 80}{Colors.ENDC}")
        
        # Active Projects Section
        projects = self.get_active_projects()
        print(f"\n{Colors.BOLD}{Colors.GREEN}📂 ACTIVE PROJECTS ({len(projects)}){Colors.ENDC}")
        print(f"{Colors.DIM}{'─' * 60}{Colors.ENDC}")
        
        if projects:
            for proj in projects:
                # Project name and status
                status_color = Colors.GREEN if not proj['errors'] else Colors.YELLOW
                print(f"  {Colors.BOLD}• {proj['name']}{Colors.ENDC}")
                print(f"    {Colors.BLUE}Phase:{Colors.ENDC} {proj['current_phase']}")
                print(f"    {Colors.BLUE}Created:{Colors.ENDC} {proj['created']}")
                
                if proj['repo_url']:
                    print(f"    {Colors.BLUE}Repo:{Colors.ENDC} {proj['repo_url']}")
                
                if proj['errors']:
                    for error in proj['errors'][:2]:  # Show max 2 errors
                        print(f"    {Colors.RED}⚠ {error}{Colors.ENDC}")
                
                print()
        else:
            print(f"  {Colors.DIM}No active projects{Colors.ENDC}")
        
        # Scheduled Phases Section
        scheduled = self.get_scheduled_phases()
        print(f"\n{Colors.BOLD}{Colors.YELLOW}⏰ SCHEDULED PHASES ({len(scheduled)}){Colors.ENDC}")
        print(f"{Colors.DIM}{'─' * 60}{Colors.ENDC}")
        
        if scheduled:
            for phase in scheduled[:5]:  # Show max 5 upcoming
                time_str = phase['run_time'].strftime("%H:%M:%S")
                mins = phase['minutes_from_now']
                
                # Color code by urgency
                if mins < 5:
                    time_color = Colors.RED
                elif mins < 15:
                    time_color = Colors.YELLOW
                else:
                    time_color = Colors.GREEN
                
                print(f"  • {Colors.BOLD}{phase['project']}{Colors.ENDC} - Phase {phase['phase']}")
                print(f"    {time_color}Runs at: {time_str} ({mins} min){Colors.ENDC}")
                print(f"    {Colors.DIM}PID: {phase['pid']}{Colors.ENDC}")
                print()
        else:
            print(f"  {Colors.DIM}No phases scheduled{Colors.ENDC}")
        
        # Webhook Status Section
        webhook = self.get_webhook_status()
        status_icon = "✅" if webhook['running'] else "❌"
        status_color = Colors.GREEN if webhook['running'] else Colors.RED
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}🔗 WEBHOOK SERVER{Colors.ENDC}")
        print(f"{Colors.DIM}{'─' * 60}{Colors.ENDC}")
        print(f"  {status_color}{status_icon} Status: {'Running' if webhook['running'] else 'Not Running'} on port {webhook['port']}{Colors.ENDC}")
        
        if webhook['recent_webhooks']:
            print(f"  {Colors.BLUE}Recent webhooks:{Colors.ENDC}")
            for wh in webhook['recent_webhooks'][-3:]:  # Show last 3
                print(f"    • {wh['time']} - {wh['repo']}")
        
        if webhook['errors']:
            print(f"  {Colors.RED}Recent errors:{Colors.ENDC}")
            for error in webhook['errors'][-2:]:  # Show last 2 errors
                print(f"    ⚠ {error[:80]}")
        
        # Duplicate Detection Section
        duplicates = self.check_duplicates()
        if duplicates:
            print(f"\n{Colors.BOLD}{Colors.RED}⚠️  DUPLICATE DETECTION{Colors.ENDC}")
            print(f"{Colors.DIM}{'─' * 60}{Colors.ENDC}")
            for dup in duplicates:
                print(f"  {Colors.RED}• {dup}{Colors.ENDC}")
        
        # System Health Section
        health = self.get_system_health()
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔧 SYSTEM HEALTH{Colors.ENDC}")
        print(f"{Colors.DIM}{'─' * 60}{Colors.ENDC}")
        
        # Health indicators
        indicators = [
            ('Webhook Server', health['webhook_server']),
            ('Orchestrator Scripts', health['orchestrator_scripts']),
            ('State Directory', health['state_directory']),
            ('GitHub SSH', health['github_ssh'])
        ]
        
        for name, status in indicators:
            icon = "✅" if status else "❌"
            color = Colors.GREEN if status else Colors.RED
            print(f"  {color}{icon} {name}{Colors.ENDC}")
        
        # Resource usage
        print(f"\n  {Colors.BLUE}Resources:{Colors.ENDC}")
        
        disk_color = Colors.GREEN if health['disk_space'] < 80 else Colors.YELLOW if health['disk_space'] < 90 else Colors.RED
        print(f"    {disk_color}Disk: {health['disk_space']}% used{Colors.ENDC}")
        
        mem_color = Colors.GREEN if health['memory_usage'] < 80 else Colors.YELLOW if health['memory_usage'] < 90 else Colors.RED
        print(f"    {mem_color}Memory: {health['memory_usage']}% used{Colors.ENDC}")
        
        # Issues Summary
        if health['issues']:
            print(f"\n{Colors.BOLD}{Colors.RED}⚠️  ISSUES DETECTED{Colors.ENDC}")
            print(f"{Colors.DIM}{'─' * 60}{Colors.ENDC}")
            for issue in health['issues']:
                print(f"  {Colors.RED}• {issue}{Colors.ENDC}")
        else:
            print(f"\n{Colors.BOLD}{Colors.GREEN}✅ All systems operational{Colors.ENDC}")
        
        # Footer
        print(f"\n{Colors.DIM}{'─' * 80}{Colors.ENDC}")
        print(f"{Colors.DIM}Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
        if watch_mode:
            print(f"{Colors.DIM}Press Ctrl+C to exit watch mode{Colors.ENDC}")
        print(f"{Colors.CYAN}{'═' * 80}{Colors.ENDC}\n")
    
    def watch(self, interval=5):
        """Watch mode - auto-refresh display"""
        try:
            while True:
                self.display_status(watch_mode=True)
                time.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Exiting watch mode...{Colors.ENDC}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='IdeaBrow Pipeline Monitor')
    parser.add_argument('-w', '--watch', action='store_true', 
                       help='Watch mode - auto-refresh every 5 seconds')
    parser.add_argument('-i', '--interval', type=int, default=5,
                       help='Refresh interval for watch mode (seconds)')
    parser.add_argument('--json', action='store_true',
                       help='Output status as JSON')
    
    args = parser.parse_args()
    
    monitor = PipelineMonitor()
    
    if args.json:
        # JSON output for integration with other tools
        status = {
            'timestamp': datetime.now().isoformat(),
            'projects': monitor.get_active_projects(),
            'scheduled_phases': [
                {
                    'pid': p['pid'],
                    'project': p['project'],
                    'phase': p['phase'],
                    'run_time': p['run_time'].isoformat(),
                    'minutes_from_now': p['minutes_from_now']
                }
                for p in monitor.get_scheduled_phases()
            ],
            'webhook': monitor.get_webhook_status(),
            'duplicates': monitor.check_duplicates(),
            'health': monitor.get_system_health()
        }
        print(json.dumps(status, indent=2))
    elif args.watch:
        monitor.watch(args.interval)
    else:
        monitor.display_status()
    
    # Return exit code based on health
    health = monitor.get_system_health()
    if health['issues']:
        return 1
    return 0

if __name__ == "__main__":
    exit(main())