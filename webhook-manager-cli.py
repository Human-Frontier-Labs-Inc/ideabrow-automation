#!/usr/bin/env python3
"""
Webhook Service Manager - Interactive UNIX Tool
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
SERVICE_PORT = 5000
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

manager = WebhookManager()

def show_status():
    """Show service status"""
    stats = manager.get_service_stats()
    
    print(f"\nWebhook Service Status:")
    print(f"  Service:     {'✓ Running' if stats['service_running'] else '✗ Stopped'} (PID: {stats['service_pid'] or 'N/A'})")
    print(f"  Tunnel:      {'✓ Active' if stats['tunnel_running'] else '✗ Down'} (PID: {stats['tunnel_pid'] or 'N/A'})")
    print(f"  Port {SERVICE_PORT}:   {'✓ Responding' if stats['port_responding'] else '✗ Not responding'}")
    
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
        print("Service is already running")
        return
    
    print("Starting webhook service...")
    os.chdir(manager.service_dir)
    
    # Start service with nohup
    cmd = f"nohup {SERVICE_CMD} > {LOG_FILE} 2>&1 &"
    subprocess.run(cmd, shell=True)
    
    # Wait for service to start
    for i in range(10):
        time.sleep(1)
        if manager.is_service_running():
            print(f"✓ Service started (PID: {manager.get_service_pid()})")
            return
    
    print("✗ Failed to start service - check logs")

@cli.command()
def stop():
    """Stop the webhook service"""
    pid = manager.get_service_pid()
    if not pid:
        print("Service is not running")
        return
    
    print(f"Stopping service (PID: {pid})...")
    try:
        os.kill(pid, 15)  # SIGTERM
        time.sleep(2)
        
        # Force kill if still running
        if manager.is_service_running():
            os.kill(pid, 9)  # SIGKILL
            time.sleep(1)
        
        if not manager.is_service_running():
            print("✓ Service stopped")
        else:
            print("✗ Failed to stop service")
    except ProcessLookupError:
        print("✓ Service was not running")
    except PermissionError:
        print("✗ Permission denied - cannot stop service")

@cli.command()
def restart():
    """Restart the webhook service"""
    print("Restarting service...")
    stop.callback()
    time.sleep(2)
    start.callback()

@cli.command()
@click.option('--lines', '-n', default=20, help='Number of lines to show')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
def logs(lines, follow):
    """Show service logs"""
    if not LOG_FILE.exists():
        print("Log file does not exist")
        return
    
    if follow:
        subprocess.run(f"tail -f {LOG_FILE}", shell=True)
    else:
        subprocess.run(f"tail -{lines} {LOG_FILE}", shell=True)

@cli.command()
def tunnel():
    """Manage cloudflared tunnel"""
    if manager.is_tunnel_running():
        print(f"Tunnel is running (PID: {manager.get_tunnel_pid()})")
        print("Run 'tunnel-stop' to stop, 'tunnel-start' to restart with new URL")
    else:
        print("Tunnel is not running")
        print("Run 'tunnel-start' to create new tunnel")

@cli.command('tunnel-start')
def tunnel_start():
    """Start cloudflared tunnel"""
    if manager.is_tunnel_running():
        print("Tunnel is already running")
        return
    
    print("Starting cloudflared tunnel...")
    print("This will show the public URL - copy it to update GitHub secrets")
    print("Press Ctrl+C to stop the tunnel")
    
    try:
        subprocess.run(f"cloudflared tunnel --url http://localhost:{SERVICE_PORT}", shell=True)
    except KeyboardInterrupt:
        print("\nTunnel stopped")

@cli.command('tunnel-stop')
def tunnel_stop():
    """Stop cloudflared tunnel"""
    pid = manager.get_tunnel_pid()
    if not pid:
        print("Tunnel is not running")
        return
    
    print(f"Stopping tunnel (PID: {pid})...")
    try:
        os.kill(pid, 15)  # SIGTERM
        time.sleep(1)
        
        if manager.is_tunnel_running():
            os.kill(pid, 9)  # SIGKILL
            time.sleep(1)
        
        if not manager.is_tunnel_running():
            print("✓ Tunnel stopped")
        else:
            print("✗ Failed to stop tunnel")
    except ProcessLookupError:
        print("✓ Tunnel was not running")

@cli.command()
def sessions():
    """Show active tmux sessions created by webhook"""
    result = subprocess.run("tmux ls 2>/dev/null", shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("No tmux sessions found")
        return
    
    webhook_sessions = []
    for line in result.stdout.strip().split('\n'):
        # Look for sessions with timestamp patterns
        if any(pattern in line for pattern in ['2025-', '2024-']):
            webhook_sessions.append(line)
    
    if webhook_sessions:
        print("Active webhook sessions:")
        for session in webhook_sessions:
            print(f"  {session}")
        print(f"\nTotal: {len(webhook_sessions)} sessions")
    else:
        print("No webhook-created sessions found")

@cli.command()
def health():
    """Check service health"""
    try:
        response = requests.get(f"http://localhost:{SERVICE_PORT}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✓ Service is healthy")
            if 'uptime' in data:
                print(f"  Uptime: {data['uptime']}s")
            if 'processed' in data:
                print(f"  Processed: {data['processed']} requests")
        else:
            print(f"✗ Service returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to service")
    except requests.exceptions.Timeout:
        print("✗ Service timeout")
    except Exception as e:
        print(f"✗ Health check failed: {e}")

@cli.command()
def state():
    """Show service state"""
    if not manager.state_file.exists():
        print("No state file found")
        return
    
    try:
        with open(manager.state_file) as f:
            state = json.load(f)
        
        print("Service State:")
        print(f"  Processed requests: {len(state.get('processed_requests', {}))}")
        print(f"  Active cooldowns: {len(state.get('project_cooldowns', {}))}")
        
        # Show recent requests
        requests_data = state.get('processed_requests', {})
        if requests_data:
            recent = sorted(requests_data.items(), key=lambda x: x[1].get('timestamp', ''))[-5:]
            print("\n  Recent requests:")
            for req_id, req_data in recent:
                timestamp = req_data.get('timestamp', 'unknown')
                project = req_data.get('project_name', 'unknown')
                print(f"    {timestamp[:19]} - {project}")
        
        # Show active cooldowns
        cooldowns = state.get('project_cooldowns', {})
        if cooldowns:
            print("\n  Active cooldowns:")
            for project, cooldown_time in cooldowns.items():
                print(f"    {project} - until {cooldown_time[:19]}")
    
    except Exception as e:
        print(f"Error reading state: {e}")

@cli.command('clear-state')
@click.confirmation_option(prompt='This will clear all service state. Continue?')
def clear_state():
    """Clear service state (processed requests and cooldowns)"""
    if manager.state_file.exists():
        manager.state_file.unlink()
        print("✓ State cleared")
    else:
        print("No state file to clear")

@cli.command()
def update():
    """Update GitHub webhook URL (helper command)"""
    print("To update the GitHub webhook URL:")
    print("1. Start tunnel: webhook-manager.py tunnel-start")
    print("2. Copy the https://...trycloudflare.com URL")
    print("3. Run this command:")
    print("   gh secret set DEV_SERVER_WEBHOOK_URL \\")
    print("     --body 'https://your-url.trycloudflare.com' \\")
    print("     --repo Human-Frontier-Labs-Inc/ideabrow-automation")

@cli.command()
def monitor():
    """Live monitoring dashboard"""
    print("Webhook Service Monitor - Press Ctrl+C to exit")
    print("=" * 50)
    
    try:
        while True:
            # Clear screen
            os.system('clear')
            
            print(f"Webhook Service Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 50)
            
            # Service status
            stats = manager.get_service_stats()
            print(f"Service:     {'✓ Running' if stats['service_running'] else '✗ Stopped'}")
            print(f"Tunnel:      {'✓ Active' if stats['tunnel_running'] else '✗ Down'}")
            print(f"Port {SERVICE_PORT}:   {'✓ OK' if stats['port_responding'] else '✗ Failed'}")
            
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
                        print(f"  {line[:80]}...")
            
            time.sleep(5)
    
    except KeyboardInterrupt:
        print("\nMonitor stopped")

if __name__ == '__main__':
    # Check if we can access the service directory
    if not SERVICE_DIR.exists():
        print(f"Error: Service directory not found: {SERVICE_DIR}")
        sys.exit(1)
    
    cli()