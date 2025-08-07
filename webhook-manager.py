#!/usr/bin/env python3
"""
Interactive Webhook Service Manager
Simple, reliable interactive script to manage the ideabrow-automation webhook service
"""

import os
import sys
import json
import subprocess
import time
import psutil
from pathlib import Path
from datetime import datetime
import requests

# Service configuration
SERVICE_NAME = "ideabrow-webhook"
SERVICE_PORT = int(os.environ.get('WEBHOOK_PORT', 8090))  # Default to 8090 like the actual service
SERVICE_DIR = Path("/home/wv3/ideabrow-automation/webhook-server")
SERVICE_CMD = "python3 webhook_server.py"
LOG_FILE = SERVICE_DIR / "webhook_server.log"
STATE_FILE = SERVICE_DIR / "webhook_state.json"

class WebhookManager:
    def __init__(self):
        self.service_dir = SERVICE_DIR
        self.log_file = LOG_FILE
        self.state_file = STATE_FILE
        
    def get_service_pid(self):
        """Get PID of running webhook service"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'python3' in proc.info['name'] and 'webhook_server.py' in ' '.join(proc.info['cmdline']):
                    return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return None
    
    def get_tunnel_pid(self):
        """Get PID of cloudflared tunnel"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'cloudflared' in proc.info['name'] and f'localhost:{SERVICE_PORT}' in ' '.join(proc.info['cmdline']):
                    return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return None
    
    def is_service_running(self):
        """Check if webhook service is running"""
        return self.get_service_pid() is not None
    
    def is_tunnel_running(self):
        """Check if tunnel is running"""
        return self.get_tunnel_pid() is not None
    
    def is_port_open(self):
        """Check if service port is responding"""
        try:
            response = requests.get(f"http://localhost:{SERVICE_PORT}/health", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def get_service_stats(self):
        """Get service statistics"""
        stats = {
            'service_running': self.is_service_running(),
            'tunnel_running': self.is_tunnel_running(),
            'port_responding': self.is_port_open(),
            'service_pid': self.get_service_pid(),
            'tunnel_pid': self.get_tunnel_pid(),
            'log_size': self.log_file.stat().st_size if self.log_file.exists() else 0,
            'uptime': None
        }
        
        # Get uptime if service is running
        if stats['service_pid']:
            try:
                proc = psutil.Process(stats['service_pid'])
                stats['uptime'] = time.time() - proc.create_time()
            except:
                pass
        
        # Get state file info
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    state = json.load(f)
                    stats['processed_requests'] = len(state.get('processed_requests', {}))
                    stats['active_cooldowns'] = len(state.get('project_cooldowns', {}))
            except:
                stats['processed_requests'] = 0
                stats['active_cooldowns'] = 0
        
        return stats

def clear_screen():
    os.system('clear')

def show_header():
    print("=" * 60)
    print("🔗 Ideabrow Webhook Service Manager")
    print("=" * 60)

def show_status():
    """Show service status"""
    stats = manager.get_service_stats()
    
    print(f"\n📊 Service Status:")
    print(f"  Service:     {'✅ Running' if stats['service_running'] else '❌ Stopped'} (PID: {stats['service_pid'] or 'N/A'})")
    print(f"  Tunnel:      {'✅ Active' if stats['tunnel_running'] else '❌ Down'} (PID: {stats['tunnel_pid'] or 'N/A'})")
    print(f"  Port {SERVICE_PORT}:   {'✅ Responding' if stats['port_responding'] else '❌ Not responding'}")
    
    if stats['uptime']:
        hours = int(stats['uptime'] // 3600)
        minutes = int((stats['uptime'] % 3600) // 60)
        print(f"  Uptime:      {hours}h {minutes}m")
    
    print(f"  Requests:    {stats.get('processed_requests', 0)} processed")
    print(f"  Cooldowns:   {stats.get('active_cooldowns', 0)} active")
    print(f"  Log size:    {stats['log_size'] // 1024}KB")

def start_service():
    """Start the webhook service"""
    if manager.is_service_running():
        print("⚠️  Service is already running")
        return
    
    print("🚀 Starting webhook service...")
    os.chdir(manager.service_dir)
    
    # Start service with nohup
    cmd = f"nohup {SERVICE_CMD} > {LOG_FILE} 2>&1 &"
    subprocess.run(cmd, shell=True)
    
    # Wait for service to start
    for i in range(10):
        time.sleep(1)
        if manager.is_service_running():
            print(f"✅ Service started (PID: {manager.get_service_pid()})")
            return
    
    print("❌ Failed to start service - check logs")

def stop_service():
    """Stop the webhook service"""
    pid = manager.get_service_pid()
    if not pid:
        print("⚠️  Service is not running")
        return
    
    print(f"🛑 Stopping service (PID: {pid})...")
    try:
        os.kill(pid, 15)  # SIGTERM
        time.sleep(2)
        
        # Force kill if still running
        if manager.is_service_running():
            os.kill(pid, 9)  # SIGKILL
            time.sleep(1)
        
        if not manager.is_service_running():
            print("✅ Service stopped")
        else:
            print("❌ Failed to stop service")
    except ProcessLookupError:
        print("✅ Service was not running")
    except PermissionError:
        print("❌ Permission denied - cannot stop service")

def restart_service():
    """Restart the webhook service"""
    print("🔄 Restarting service...")
    stop_service()
    time.sleep(2)
    start_service()

def show_logs():
    """Show service logs"""
    if not LOG_FILE.exists():
        print("❌ Log file does not exist")
        return
    
    print("\n📋 Recent logs (last 20 lines):")
    print("-" * 60)
    subprocess.run(f"tail -20 {LOG_FILE}", shell=True)

def show_sessions():
    """Show active tmux sessions created by webhook"""
    result = subprocess.run("tmux ls 2>/dev/null", shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ No tmux sessions found")
        return
    
    webhook_sessions = []
    for line in result.stdout.strip().split('\n'):
        # Look for sessions with timestamp patterns
        if any(pattern in line for pattern in ['2025-', '2024-']):
            webhook_sessions.append(line)
    
    if webhook_sessions:
        print(f"\n🖥️  Active webhook sessions ({len(webhook_sessions)}):")
        for session in webhook_sessions:
            print(f"  {session}")
    else:
        print("❌ No webhook-created sessions found")

def manage_tunnel():
    """Tunnel management submenu"""
    while True:
        clear_screen()
        show_header()
        print("\n🌐 Tunnel Management")
        
        if manager.is_tunnel_running():
            print(f"Status: ✅ Running (PID: {manager.get_tunnel_pid()})")
        else:
            print("Status: ❌ Not running")
        
        print("\nOptions:")
        print("1. Start tunnel")
        print("2. Stop tunnel")
        print("3. Show GitHub secret update command")
        print("0. Back to main menu")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '1':
            start_tunnel()
        elif choice == '2':
            stop_tunnel()
        elif choice == '3':
            show_update_command()
        elif choice == '0':
            break
        else:
            print("❌ Invalid choice")
        
        input("\nPress Enter to continue...")

def start_tunnel():
    """Start cloudflared tunnel"""
    if manager.is_tunnel_running():
        print("⚠️  Tunnel is already running")
        return
    
    print("🚇 Starting cloudflared tunnel...")
    print("📋 Copy the URL that appears to update GitHub secrets")
    print("⚠️  Press Ctrl+C to stop the tunnel\n")
    
    try:
        subprocess.run(f"cloudflared tunnel --url http://localhost:{SERVICE_PORT}", shell=True)
    except KeyboardInterrupt:
        print("\n🛑 Tunnel stopped")

def stop_tunnel():
    """Stop cloudflared tunnel"""
    pid = manager.get_tunnel_pid()
    if not pid:
        print("⚠️  Tunnel is not running")
        return
    
    print(f"🛑 Stopping tunnel (PID: {pid})...")
    try:
        os.kill(pid, 15)  # SIGTERM
        time.sleep(1)
        
        if manager.is_tunnel_running():
            os.kill(pid, 9)  # SIGKILL
            time.sleep(1)
        
        if not manager.is_tunnel_running():
            print("✅ Tunnel stopped")
        else:
            print("❌ Failed to stop tunnel")
    except ProcessLookupError:
        print("✅ Tunnel was not running")

def show_update_command():
    """Show GitHub webhook URL update command"""
    print("\n📝 To update GitHub webhook URL:")
    print("1. Start tunnel and copy the https://...trycloudflare.com URL")
    print("2. Run this command:")
    print("   gh secret set DEV_SERVER_WEBHOOK_URL \\")
    print("     --body 'https://your-url.trycloudflare.com' \\")
    print("     --repo Human-Frontier-Labs-Inc/ideabrow-automation")

def show_phases():
    """Show upcoming phases and scheduled commands"""
    print(f"\n🔄 Phase Status & Upcoming Commands:")
    
    # Check for active tmux sessions with phases
    result = subprocess.run("tmux ls 2>/dev/null", shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ No tmux sessions found")
        return
    
    webhook_sessions = []
    for line in result.stdout.strip().split('\n'):
        if any(pattern in line for pattern in ['2025-', '2024-']):
            session_name = line.split(':')[0]
            webhook_sessions.append(session_name)
    
    if not webhook_sessions:
        print("❌ No active webhook sessions")
        return
    
    print(f"📊 Found {len(webhook_sessions)} active sessions:")
    
    for session in webhook_sessions:
        print(f"\n🖥️  Session: {session}")
        
        # Check for phase files in projects directory
        project_dir = Path(f"/home/wv3/projects/{session}")
        if project_dir.exists():
            # Look for phase status files
            phase_files = list(project_dir.glob("phase_*.status"))
            progress_file = project_dir / "PROGRESS_TRACKER.md"
            
            if progress_file.exists():
                print(f"  📋 Progress tracker: Found")
                # Try to extract current phase from tracker
                try:
                    content = progress_file.read_text()
                    lines = content.split('\n')
                    current_phase = "Phase 1"
                    for line in lines:
                        if '- [x]' in line and 'Phase' in line:
                            # Find completed phases
                            if 'Phase 2' in line:
                                current_phase = "Phase 3"
                            elif 'Phase 3' in line:
                                current_phase = "Phase 4"
                            elif 'Phase 4' in line:
                                current_phase = "Phase 5"
                            elif 'Phase 5' in line:
                                current_phase = "Complete"
                    print(f"  🎯 Current phase: {current_phase}")
                except:
                    print(f"  ⚠️  Could not parse progress")
            
            # Check for scheduled commands
            nohup_files = list(project_dir.glob("nohup_*.out"))
            if nohup_files:
                print(f"  ⏰ Scheduled processes: {len(nohup_files)}")
                for nf in nohup_files[-2:]:  # Show last 2
                    print(f"    📄 {nf.name}")
            
            # Check recent activity
            if project_dir.exists():
                try:
                    mtime = project_dir.stat().st_mtime
                    last_modified = datetime.fromtimestamp(mtime)
                    time_diff = datetime.now() - last_modified
                    if time_diff.total_seconds() < 3600:  # Less than 1 hour
                        print(f"  🕒 Last activity: {int(time_diff.total_seconds() / 60)}m ago")
                    else:
                        print(f"  🕒 Last activity: {int(time_diff.total_seconds() / 3600)}h ago")
                except:
                    pass
        else:
            print(f"  ❌ Project directory not found")

def show_state():
    """Show service state and webhook activity"""
    print(f"\n📈 Service State:")
    
    # Basic state from state file
    if manager.state_file.exists():
        try:
            with open(manager.state_file) as f:
                state = json.load(f)
            
            processed = len(state.get('processed_requests', {}))
            cooldowns = len(state.get('project_cooldowns', {}))
            print(f"  Processed requests: {processed}")
            print(f"  Active cooldowns: {cooldowns}")
            
            # Show recent requests
            requests_data = state.get('processed_requests', {})
            if requests_data:
                recent = sorted(requests_data.items(), key=lambda x: x[1].get('timestamp', ''))[-3:]
                print("\n  Recent requests:")
                for req_id, req_data in recent:
                    timestamp = req_data.get('timestamp', 'unknown')[:16]
                    project = req_data.get('project_name', 'unknown')
                    print(f"    {timestamp} - {project}")
        
        except Exception as e:
            print(f"❌ Error reading state: {e}")
    else:
        print("  No state file found")
    
    # Show GitHub Actions activity
    print(f"\n🔗 Recent GitHub Activity:")
    processed_dir = Path("/home/wv3/ideabrow-automation/processed")
    if processed_dir.exists():
        recent_projects = sorted(processed_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:3]
        if recent_projects:
            for project in recent_projects:
                mtime = datetime.fromtimestamp(project.stat().st_mtime)
                print(f"  📦 {project.name} - {mtime.strftime('%m-%d %H:%M')}")
        else:
            print("  No processed projects found")
    else:
        print("  No processed directory found")

def clear_state():
    """Clear service state"""
    if not manager.state_file.exists():
        print("❌ No state file to clear")
        return
    
    confirm = input("⚠️  This will clear all service state. Continue? (y/N): ").strip().lower()
    if confirm == 'y':
        manager.state_file.unlink()
        print("✅ State cleared")
    else:
        print("❌ Cancelled")

def live_monitor():
    """Live monitoring dashboard"""
    print("🔄 Starting live monitor - Press Ctrl+C to exit")
    print("=" * 50)
    
    try:
        while True:
            clear_screen()
            show_header()
            
            print(f"Live Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            
            # Service status
            stats = manager.get_service_stats()
            print(f"Service:     {'✅ Running' if stats['service_running'] else '❌ Stopped'}")
            print(f"Tunnel:      {'✅ Active' if stats['tunnel_running'] else '❌ Down'}")
            print(f"Port {SERVICE_PORT}:   {'✅ OK' if stats['port_responding'] else '❌ Failed'}")
            
            if stats['uptime']:
                hours = int(stats['uptime'] // 3600)
                minutes = int((stats['uptime'] % 3600) // 60)
                print(f"Uptime:      {hours}h {minutes}m")
            
            print(f"Requests:    {stats.get('processed_requests', 0)}")
            print(f"Cooldowns:   {stats.get('active_cooldowns', 0)}")
            
            # Recent log entries
            if LOG_FILE.exists():
                print("\nRecent logs:")
                result = subprocess.run(f"tail -3 {LOG_FILE}", shell=True, capture_output=True, text=True)
                for line in result.stdout.strip().split('\n')[-3:]:
                    if line.strip():
                        print(f"  {line[:70]}...")
            
            print("\nPress Ctrl+C to exit...")
            time.sleep(5)
    
    except KeyboardInterrupt:
        print("\n🛑 Monitor stopped")

def main_menu():
    """Main interactive menu"""
    while True:
        clear_screen()
        show_header()
        show_status()
        
        print(f"\n📋 Main Menu:")
        print("1. Show phases & upcoming commands")
        print("2. Show logs")
        print("3. Show state & activity")
        print("4. Restart service")
        print("5. Manage tunnel")
        print("0. Exit")
        
        choice = input("\nEnter choice (0-5): ").strip()
        
        if choice == '1':
            show_phases()
        elif choice == '2':
            show_logs()
        elif choice == '3':
            show_state()
        elif choice == '4':
            restart_service()
        elif choice == '5':
            manage_tunnel()
        elif choice == '0':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")
        
        if choice != '5' and choice != '0':  # Don't pause for submenus
            input("\nPress Enter to continue...")

if __name__ == '__main__':
    # Check if we can access the service directory
    if not SERVICE_DIR.exists():
        print(f"❌ Error: Service directory not found: {SERVICE_DIR}")
        sys.exit(1)
    
    # Initialize manager
    manager = WebhookManager()
    
    # Run interactive menu
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)