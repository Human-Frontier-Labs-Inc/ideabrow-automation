#!/usr/bin/env python3
"""
IdeaBrow Pipeline - Real-time Phase Tracker
Shows live updates of phase execution across all projects
"""

import subprocess
import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import argparse
import signal

# ANSI color codes
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
    
    # Animation characters
    SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

class PhaseTracker:
    def __init__(self):
        self.state_dir = Path("/home/wv3/ideabrow-pipeline/webhook-server/state")
        self.spinner_index = 0
        self.last_update = {}
        self.phase_history = {}
        
    def get_project_phases(self, project_name: str) -> Optional[Dict]:
        """Get current phase information for a project"""
        tracker_file = self.state_dir / f"{project_name}_tracker.json"
        
        if not tracker_file.exists():
            return None
            
        try:
            with open(tracker_file) as f:
                tracker = json.load(f)
                
            phases = tracker.get('phases', [])
            
            # Find current phase
            current_phase = None
            completed_count = 0
            
            for phase in phases:
                if phase.get('status') == 'completed':
                    completed_count += 1
                elif phase.get('status') == 'in_progress':
                    current_phase = phase
                    
            return {
                'total': len(phases),
                'completed': completed_count,
                'current': current_phase,
                'phases': phases,
                'progress_percent': int((completed_count / len(phases) * 100)) if phases else 0
            }
            
        except Exception as e:
            return None
    
    def get_active_projects(self) -> List[str]:
        """Get list of active project sessions"""
        try:
            result = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name}"],
                capture_output=True,
                text=True,
                stderr=subprocess.DEVNULL
            )
            
            sessions = []
            for session in result.stdout.strip().split('\n'):
                if session and session not in ['server', 'tmux-orc']:
                    # Verify Claude is running
                    pane_check = subprocess.run(
                        ["tmux", "list-panes", "-t", f"{session}:0", "-F", "#{pane_current_command}"],
                        capture_output=True,
                        text=True,
                        stderr=subprocess.DEVNULL
                    )
                    if 'claude' in pane_check.stdout.lower():
                        sessions.append(session)
                        
            return sessions
            
        except:
            return []
    
    def get_recent_activity(self, project_name: str, lines: int = 3) -> List[str]:
        """Get recent activity from tmux pane"""
        try:
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", f"{project_name}:0", "-p", "-S", f"-{lines}"],
                capture_output=True,
                text=True,
                stderr=subprocess.DEVNULL
            )
            
            if result.stdout:
                return [line.strip() for line in result.stdout.split('\n') if line.strip()]
                
        except:
            pass
            
        return []
    
    def render_progress_bar(self, percent: int, width: int = 30) -> str:
        """Render a progress bar"""
        filled = int(width * percent / 100)
        empty = width - filled
        
        if percent == 100:
            color = Colors.GREEN
        elif percent > 50:
            color = Colors.YELLOW
        else:
            color = Colors.CYAN
            
        bar = f"{color}{'█' * filled}{Colors.DIM}{'░' * empty}{Colors.ENDC}"
        return f"[{bar}] {percent}%"
    
    def detect_phase_changes(self, project: str, current_data: Dict) -> Optional[str]:
        """Detect if phase has changed since last check"""
        if project not in self.last_update:
            self.last_update[project] = current_data
            return None
            
        last = self.last_update[project]
        
        # Check for phase completion
        if last['completed'] < current_data['completed']:
            completed_phase = None
            for phase in current_data['phases']:
                if phase.get('status') == 'completed':
                    phase_num = phase.get('phase_number', '?')
                    if phase_num not in self.phase_history.get(project, set()):
                        completed_phase = phase
                        if project not in self.phase_history:
                            self.phase_history[project] = set()
                        self.phase_history[project].add(phase_num)
                        
            if completed_phase:
                self.last_update[project] = current_data
                return f"✅ Completed: Phase {completed_phase.get('phase_number', '?')} - {completed_phase.get('name', 'Unknown')}"
        
        # Check for new phase start
        if (last['current'] and current_data['current'] and 
            last['current'].get('phase_number') != current_data['current'].get('phase_number')):
            self.last_update[project] = current_data
            new_phase = current_data['current']
            return f"🚀 Started: Phase {new_phase.get('phase_number', '?')} - {new_phase.get('name', 'Unknown')}"
            
        self.last_update[project] = current_data
        return None
    
    def display_tracker(self, show_activity: bool = False):
        """Display the phase tracker dashboard"""
        os.system('clear')
        
        # Header with spinner
        spinner = Colors.SPINNER[self.spinner_index % len(Colors.SPINNER)]
        self.spinner_index += 1
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}          IDEABROW PIPELINE - REAL-TIME PHASE TRACKER {spinner}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 80}{Colors.ENDC}")
        print(f"{Colors.DIM}Last Update: {datetime.now().strftime('%H:%M:%S')} | Press Ctrl+C to exit{Colors.ENDC}")
        print()
        
        projects = self.get_active_projects()
        
        if not projects:
            print(f"{Colors.YELLOW}No active projects found{Colors.ENDC}")
            return
            
        # Track events for notification area
        events = []
        
        for project in sorted(projects):
            phase_data = self.get_project_phases(project)
            
            if not phase_data:
                continue
                
            # Check for changes
            change = self.detect_phase_changes(project, phase_data)
            if change:
                events.append(f"{Colors.BOLD}{project}:{Colors.ENDC} {change}")
            
            # Project header
            print(f"{Colors.BOLD}{Colors.GREEN}📂 {project}{Colors.ENDC}")
            
            # Progress bar
            progress_bar = self.render_progress_bar(phase_data['progress_percent'])
            print(f"   Progress: {progress_bar} ({phase_data['completed']}/{phase_data['total']} phases)")
            
            # Current phase
            if phase_data['current']:
                current = phase_data['current']
                phase_num = current.get('phase_number', '?')
                phase_name = current.get('name', 'Unknown')[:50]
                
                # Animated indicator for current phase
                anim = Colors.SPINNER[self.spinner_index % len(Colors.SPINNER)]
                print(f"   {Colors.YELLOW}{anim} Current:{Colors.ENDC} Phase {phase_num} - {phase_name}")
                
                # Show start time if available
                if 'started_at' in current:
                    try:
                        started = datetime.fromisoformat(current['started_at'])
                        duration = datetime.now() - started
                        mins = int(duration.total_seconds() / 60)
                        secs = int(duration.total_seconds() % 60)
                        print(f"   {Colors.DIM}Running for: {mins}m {secs}s{Colors.ENDC}")
                    except:
                        pass
            else:
                if phase_data['completed'] == phase_data['total']:
                    print(f"   {Colors.GREEN}✅ All phases completed!{Colors.ENDC}")
                else:
                    print(f"   {Colors.DIM}⏸ Waiting for next phase...{Colors.ENDC}")
            
            # Show recent activity if enabled
            if show_activity:
                activity = self.get_recent_activity(project, 2)
                if activity:
                    print(f"   {Colors.DIM}Recent activity:{Colors.ENDC}")
                    for line in activity:
                        if len(line) > 60:
                            line = line[:57] + "..."
                        print(f"     {Colors.DIM}{line}{Colors.ENDC}")
            
            print()
        
        # Show scheduled phases
        scheduled = self.get_scheduled_phases()
        if scheduled:
            print(f"{Colors.BOLD}{Colors.YELLOW}⏰ Upcoming Phases:{Colors.ENDC}")
            for item in scheduled[:3]:  # Show next 3
                mins = item['minutes_from_now']
                if mins < 1:
                    time_str = f"{Colors.RED}< 1 minute{Colors.ENDC}"
                elif mins < 5:
                    time_str = f"{Colors.YELLOW}{mins} minutes{Colors.ENDC}"
                else:
                    time_str = f"{Colors.GREEN}{mins} minutes{Colors.ENDC}"
                    
                print(f"   • {item['project']} Phase {item['phase']} in {time_str}")
            print()
        
        # Show recent events
        if events:
            print(f"{Colors.BOLD}{Colors.CYAN}📢 Recent Events:{Colors.ENDC}")
            for event in events[-5:]:  # Show last 5 events
                print(f"   {event}")
            print()
    
    def get_scheduled_phases(self) -> List[Dict]:
        """Get scheduled phases"""
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )
            
            scheduled = []
            for line in result.stdout.split('\n'):
                if 'sleep' in line and 'PHASE' in line:
                    import re
                    
                    sleep_match = re.search(r'sleep (\d+)', line)
                    proj_match = re.search(r'(\S+):0', line)
                    phase_match = re.search(r'PHASE (\d+)', line)
                    
                    if sleep_match and proj_match and phase_match:
                        scheduled.append({
                            'project': proj_match.group(1),
                            'phase': phase_match.group(1),
                            'minutes_from_now': int(sleep_match.group(1)) // 60
                        })
            
            return sorted(scheduled, key=lambda x: x['minutes_from_now'])
            
        except:
            return []
    
    def run(self, interval: float = 2.0, show_activity: bool = False):
        """Run the tracker in continuous mode"""
        def signal_handler(sig, frame):
            print(f"\n{Colors.YELLOW}Stopping phase tracker...{Colors.ENDC}")
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            while True:
                self.display_tracker(show_activity)
                time.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Phase tracker stopped{Colors.ENDC}")

def main():
    parser = argparse.ArgumentParser(description='Real-time Phase Tracker for IdeaBrow Pipeline')
    parser.add_argument('-i', '--interval', type=float, default=2.0,
                       help='Update interval in seconds (default: 2.0)')
    parser.add_argument('-a', '--activity', action='store_true',
                       help='Show recent activity from tmux panes')
    parser.add_argument('--once', action='store_true',
                       help='Run once and exit (no continuous updates)')
    
    args = parser.parse_args()
    
    tracker = PhaseTracker()
    
    if args.once:
        tracker.display_tracker(args.activity)
    else:
        print(f"{Colors.CYAN}Starting real-time phase tracker...{Colors.ENDC}")
        print(f"{Colors.DIM}Update interval: {args.interval}s | Press Ctrl+C to stop{Colors.ENDC}")
        time.sleep(1)
        tracker.run(args.interval, args.activity)

if __name__ == "__main__":
    main()