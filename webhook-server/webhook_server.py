#!/usr/bin/env python3
"""
Enhanced Webhook Server for GitHub Actions Integration
Receives webhook from ideabrow-automation and triggers tmux session creation
Features: deduplication, state management, cooldown protection
"""

import os
import sys
import json
import logging
import subprocess
import hashlib
import uuid
from flask import Flask, request, jsonify
from pathlib import Path
from datetime import datetime, timedelta
import threading
import time

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent.parent / "scripts"))
try:
    from select_template_enhanced import select_template
except ImportError:
    try:
        from select_template import select_template
    except ImportError:
        # Fallback - create dummy function if script not available
        def select_template(requirements='', template_hint=None):
            return {
                'template': 'modern-saas/nextjs-saas-clerk', 
                'full_path': '/home/wv3/templates/modern-saas/nextjs-saas-clerk',
                'auth': 'Clerk',
                'database': 'Prisma/SQLite',
                'ui': 'shadcn/ui'
            }

# Add current directory to path for local modules
sys.path.append(str(Path(__file__).parent))
from webhook_adapter import transform_webhook_payload
from phase_scheduler import create_phase_scheduler

# Configure logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
PORT = int(os.environ.get('WEBHOOK_PORT', 8090))
HOST = '0.0.0.0'
SCRIPTS_DIR = Path("/home/wv3/tmux-automation/scripts")
STATE_DIR = Path(__file__).parent / "state"
STATE_DIR.mkdir(exist_ok=True)

# State tracking
REQUEST_STATE_FILE = STATE_DIR / "processed_requests.json"
PROJECT_COOLDOWN_FILE = STATE_DIR / "project_cooldowns.json"
COOLDOWN_MINUTES = 5  # Reject webhooks for projects created in last 5 minutes

class WebhookStateManager:
    """Manages webhook request state and deduplication"""
    
    def __init__(self):
        self.processed_requests = self._load_processed_requests()
        self.project_cooldowns = self._load_project_cooldowns()
    
    def _load_processed_requests(self):
        """Load processed request IDs from state file"""
        try:
            if REQUEST_STATE_FILE.exists():
                with open(REQUEST_STATE_FILE, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading processed requests: {e}")
            return {}
    
    def _save_processed_requests(self):
        """Save processed request IDs to state file"""
        try:
            with open(REQUEST_STATE_FILE, 'w') as f:
                json.dump(self.processed_requests, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processed requests: {e}")
    
    def _load_project_cooldowns(self):
        """Load project cooldown timestamps"""
        try:
            if PROJECT_COOLDOWN_FILE.exists():
                with open(PROJECT_COOLDOWN_FILE, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading project cooldowns: {e}")
            return {}
    
    def _save_project_cooldowns(self):
        """Save project cooldown timestamps"""
        try:
            with open(PROJECT_COOLDOWN_FILE, 'w') as f:
                json.dump(self.project_cooldowns, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving project cooldowns: {e}")
    
    def generate_request_id(self, project_name, timestamp=None):
        """Generate unique request ID based on project name and timestamp"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # Create hash from project name and timestamp
        data = f"{project_name}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def is_duplicate_request(self, request_id):
        """Check if request has already been processed"""
        return request_id in self.processed_requests
    
    def mark_request_processed(self, request_id, project_name):
        """Mark request as processed"""
        self.processed_requests[request_id] = {
            'project_name': project_name,
            'timestamp': datetime.now().isoformat(),
            'processed': True
        }
        self._save_processed_requests()
        logger.info(f"Marked request {request_id} as processed for project {project_name}")
    
    def is_project_in_cooldown(self, project_name):
        """Check if project is in cooldown period"""
        if project_name not in self.project_cooldowns:
            return False
        
        last_created = datetime.fromisoformat(self.project_cooldowns[project_name])
        cooldown_end = last_created + timedelta(minutes=COOLDOWN_MINUTES)
        
        return datetime.now() < cooldown_end
    
    def get_cooldown_remaining(self, project_name):
        """Get remaining cooldown time in minutes"""
        if project_name not in self.project_cooldowns:
            return 0
        
        last_created = datetime.fromisoformat(self.project_cooldowns[project_name])
        cooldown_end = last_created + timedelta(minutes=COOLDOWN_MINUTES)
        remaining = cooldown_end - datetime.now()
        
        return max(0, remaining.total_seconds() / 60)
    
    def set_project_cooldown(self, project_name):
        """Set cooldown for project"""
        self.project_cooldowns[project_name] = datetime.now().isoformat()
        self._save_project_cooldowns()
        logger.info(f"Set {COOLDOWN_MINUTES}-minute cooldown for project {project_name}")
    
    def cleanup_old_entries(self, days_old=7):
        """Clean up entries older than specified days"""
        cutoff = datetime.now() - timedelta(days=days_old)
        
        # Clean processed requests
        old_requests = []
        for req_id, data in self.processed_requests.items():
            if datetime.fromisoformat(data['timestamp']) < cutoff:
                old_requests.append(req_id)
        
        for req_id in old_requests:
            del self.processed_requests[req_id]
        
        if old_requests:
            self._save_processed_requests()
            logger.info(f"Cleaned up {len(old_requests)} old processed requests")
        
        # Clean project cooldowns
        old_projects = []
        for project_name, timestamp in self.project_cooldowns.items():
            if datetime.fromisoformat(timestamp) < cutoff:
                old_projects.append(project_name)
        
        for project_name in old_projects:
            del self.project_cooldowns[project_name]
        
        if old_projects:
            self._save_project_cooldowns()
            logger.info(f"Cleaned up {len(old_projects)} old project cooldowns")

# Initialize state manager
state_manager = WebhookStateManager()

def clean_project_name(name):
    """Clean and standardize project name with full timestamp"""
    # Keep original timestamp precision, don't truncate
    cleaned = name.replace(' ', '-').lower()
    cleaned = ''.join(c for c in cleaned if c.isalnum() or c in '-_')
    
    # Don't truncate - allow full timestamp-based names
    return cleaned

def initialize_orchestrator(project_name, session_params):
    """
    Initialize orchestrator by sending PM instructions to Claude
    This sends a message to Claude to read PROGRESS_TRACKER.md and manage development
    """
    try:
        logger.info(f"Initializing orchestrator for project: {project_name}")
        
        # Construct the PM message for Claude (without starter prompt)
        pm_message = f"""PROJECT MANAGER INITIALIZATION

You are now the Project Manager for: {project_name}

IMMEDIATE ACTIONS REQUIRED:
1. FIRST: Run the template and analyze what it already provides
2. Read PROGRESS_TRACKER.md but ADAPT it - the template already has auth, DB, etc.
3. Focus on EXTENDING the template, not rebuilding from scratch
4. If template has Clerk, use it. If it has Prisma, use it. Work WITH the template!

PROJECT DETAILS:
- Project Name: {project_name}
- Template Used: {session_params.get('template_name', 'N/A')}
- GitHub Repository: {session_params.get('github_repo', 'N/A')}
- Created: {session_params.get('timestamp', 'N/A')}

Please start by reading PROGRESS_TRACKER.md and then coordinate the development workflow."""

        # Call the send-claude-message script
        script_path = "/home/wv3/.claude/orchestrator/send-claude-message.sh"
        
        cmd = [script_path, f"{project_name}:0", pm_message]
        
        logger.info(f"Sending PM initialization message to Claude via: {script_path}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info(f"Successfully initialized orchestrator for {project_name}")
            logger.debug(f"Claude response: {result.stdout}")
            
            # Now send the starter prompt as a separate message
            starter_prompt = session_params.get('starter_prompt')
            if starter_prompt:
                logger.info(f"Sending starter prompt to Claude for {project_name}")
                
                # Wait a bit for PM initialization to complete
                time.sleep(3)
                
                # Send starter prompt
                starter_cmd = [script_path, f"{project_name}:0", starter_prompt]
                starter_result = subprocess.run(starter_cmd, capture_output=True, text=True, timeout=30)
                
                if starter_result.returncode == 0:
                    logger.info(f"Successfully sent starter prompt for {project_name}")
                    
                    # Schedule all development phases after successful initialization
                    logger.info(f"Scheduling development phases for {project_name}")
                    phase_scheduler = create_phase_scheduler()
                    phase_success = phase_scheduler.schedule_all_phases(project_name, session_params)
                    
                    if phase_success:
                        logger.info(f"Successfully scheduled all phases for {project_name}")
                    else:
                        logger.error(f"Failed to schedule phases for {project_name}")
                        
                else:
                    logger.error(f"Failed to send starter prompt for {project_name}: {starter_result.stderr}")
        else:
            logger.error(f"Failed to initialize orchestrator for {project_name}: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout while initializing orchestrator for {project_name}")
    except Exception as e:
        logger.error(f"Error initializing orchestrator for {project_name}: {e}")

def create_tmux_session(project_data):
    """
    Create tmux session in background thread
    """
    try:
        logger.info(f"Creating tmux session for project: {project_data['project_name']}")
        
        # Step 1: Select template
        logger.info("Selecting template...")
        template_result = select_template(
            requirements=project_data.get('requirements_summary', ''),
            template_hint=project_data.get('template_hint')
        )
        logger.info(f"Selected template: {template_result['template']}")
        
        # Step 2: Prepare parameters for tmux script
        template_path = template_result.get('full_path', f"/home/wv3/templates/{template_result['template']}")
        
        # Use full repo URL for cloning
        # Try original_repo_url first (from transformed webhook), then repo_url, then github_repo
        github_repo = project_data.get('original_repo_url', 
                                     project_data.get('repo_url', 
                                     project_data.get('github_repo', '')))
        
        session_params = {
            "project_name": project_data['project_name'],
            "template_path": template_path,
            "template_name": template_result['template'],
            "github_repo": github_repo,
            "progress_tracker": project_data.get('progress_tracker_content', ''),
            "starter_prompt": project_data.get('starter_prompt', ''),
            "timestamp": datetime.now().isoformat(),
            "request_id": project_data.get('request_id', 'unknown')
        }
        
        # Step 3: Save session parameters
        session_file = STATE_DIR / f"{project_data['project_name']}_params.json"
        with open(session_file, 'w') as f:
            json.dump(session_params, f, indent=2)
        logger.info(f"Saved session parameters to: {session_file}")
        
        # Step 4: Call the tmux creation script
        cmd = [
            str(SCRIPTS_DIR / "create_automated_session.sh"),
            project_data['project_name'],
            template_path,
            str(session_file)
        ]
        
        logger.info(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Successfully created tmux session: {result.stdout}")
            
            # Set cooldown for this project
            state_manager.set_project_cooldown(project_data['project_name'])
            
            # Initialize orchestrator after successful session creation
            initialize_orchestrator(project_data['project_name'], session_params)
            
            return {"success": True, "session_name": project_data['project_name']}
        else:
            logger.error(f"Failed to create tmux session: {result.stderr}")
            return {"success": False, "error": result.stderr}
            
    except Exception as e:
        logger.error(f"Error creating tmux session: {e}")
        return {"success": False, "error": str(e)}

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "port": PORT,
        "state_manager": "active",
        "cooldown_minutes": COOLDOWN_MINUTES
    })

@app.route('/', methods=['POST'])  # Also accept webhooks at root
@app.route('/webhook', methods=['POST'])
@app.route('/webhook/<token>', methods=['POST'])
def webhook(token=None):
    """
    Main webhook endpoint with deduplication and state management
    Expected payload:
    {
        "project_name": "my-app",
        "requirements_summary": "Build a blog with...",
        "template_hint": "vercel/blog",  # optional
        "github_repo": "user/repo",
        "progress_tracker_content": "# Project: Blog\n...",
        "starter_prompt": "Begin by implementing..."  # optional
    }
    """
    # Log the token for debugging
    if token:
        logger.info(f"Webhook called with token: {token}")
    return handle_webhook_request(request.json)

@app.route('/status/<project_name>', methods=['GET'])
def status(project_name):
    """Check status of a project session with cooldown info"""
    try:
        # Check if tmux session exists
        result = subprocess.run(
            ['tmux', 'has-session', '-t', project_name],
            capture_output=True
        )
        
        session_exists = result.returncode == 0
        
        # Check for state file
        state_file = STATE_DIR / f"{project_name}_params.json"
        has_state = state_file.exists()
        
        # Check cooldown status
        in_cooldown = state_manager.is_project_in_cooldown(project_name)
        cooldown_remaining = state_manager.get_cooldown_remaining(project_name)
        
        return jsonify({
            "project_name": project_name,
            "session_exists": session_exists,
            "has_state": has_state,
            "state_file": str(state_file) if has_state else None,
            "in_cooldown": in_cooldown,
            "cooldown_remaining_minutes": round(cooldown_remaining, 2) if in_cooldown else 0
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/test', methods=['POST'])
def test_endpoint():
    """Test endpoint for manual testing"""
    test_data = {
        "project_name": "test-blog",
        "requirements_summary": "Build a simple blog with markdown support",
        "template_hint": None,
        "github_repo": "test/test-blog",
        "progress_tracker_content": "# Project: Test Blog\n\n## Phase 1: Setup\n- Initialize project\n- Set up database",
        "starter_prompt": "Let's build a blog application. Start by setting up the project structure."
    }
    
    # Override with any provided data
    if request.json:
        test_data.update(request.json)
    
    logger.info("Test endpoint called")
    
    # Call webhook handler directly with test data
    return handle_webhook_request(test_data)

@app.route('/admin/cleanup', methods=['POST'])
def admin_cleanup():
    """Admin endpoint to clean up old state entries"""
    try:
        days = request.json.get('days', 7) if request.json else 7
        state_manager.cleanup_old_entries(days)
        return jsonify({"status": "cleaned", "days": days})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/state', methods=['GET'])
def admin_state():
    """Admin endpoint to view current state"""
    try:
        return jsonify({
            "processed_requests": len(state_manager.processed_requests),
            "project_cooldowns": len(state_manager.project_cooldowns),
            "cooldown_minutes": COOLDOWN_MINUTES,
            "active_cooldowns": {
                name: round(state_manager.get_cooldown_remaining(name), 2)
                for name in state_manager.project_cooldowns.keys()
                if state_manager.is_project_in_cooldown(name)
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def handle_webhook_request(data):
    """Handle webhook request with enhanced deduplication and state management"""
    try:
        # Check if this is from ideabrow-automation (has repo_url)
        if 'repo_url' in data and 'tracker_url' in data:
            logger.info("Detected ideabrow-automation webhook, transforming...")
            data = transform_webhook_payload(data)
        
        # Generate request ID for deduplication
        project_name = data.get('project_name', 'unknown')
        timestamp = data.get('original_timestamp') or datetime.now().isoformat()
        request_id = state_manager.generate_request_id(project_name, timestamp)
        
        logger.info(f"Received webhook: {project_name} (request_id: {request_id})")
        
        # Check for duplicate request
        if state_manager.is_duplicate_request(request_id):
            logger.warning(f"Duplicate request detected for {project_name}, request_id: {request_id}")
            return jsonify({
                "status": "duplicate",
                "message": f"Request already processed",
                "project_name": project_name,
                "request_id": request_id
            }), 409
        
        # Validate required fields
        required = ['project_name', 'requirements_summary']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({
                "error": f"Missing required fields: {missing}",
                "request_id": request_id
            }), 400
        
        # Clean project name (preserve full timestamp)
        cleaned_project_name = clean_project_name(data['project_name'])
        data['project_name'] = cleaned_project_name
        data['request_id'] = request_id
        
        # Check cooldown period
        if state_manager.is_project_in_cooldown(cleaned_project_name):
            cooldown_remaining = state_manager.get_cooldown_remaining(cleaned_project_name)
            logger.warning(f"Project {cleaned_project_name} is in cooldown, {cooldown_remaining:.1f} minutes remaining")
            return jsonify({
                "status": "cooldown",
                "message": f"Project in cooldown period",
                "project_name": cleaned_project_name,
                "cooldown_remaining_minutes": round(cooldown_remaining, 2),
                "request_id": request_id
            }), 429
        
        # Mark request as processed BEFORE starting work
        state_manager.mark_request_processed(request_id, cleaned_project_name)
        
        # Create session in background thread
        thread = threading.Thread(
            target=lambda: create_tmux_session(data),
            daemon=True
        )
        thread.start()
        
        return jsonify({
            "status": "accepted",
            "message": f"Creating tmux session for {data['project_name']}",
            "project_name": data['project_name'],
            "request_id": request_id,
            "cooldown_minutes": COOLDOWN_MINUTES
        }), 202
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        request_id = locals().get('request_id', 'unknown')
        return jsonify({
            "error": str(e),
            "request_id": request_id
        }), 500

if __name__ == '__main__':
    logger.info(f"Starting enhanced webhook server on {HOST}:{PORT}")
    logger.info(f"Webhook URL: http://{HOST}:{PORT}/webhook")
    logger.info(f"Health check: http://{HOST}:{PORT}/health")
    logger.info(f"Test endpoint: http://{HOST}:{PORT}/test")
    logger.info(f"Admin endpoints: /admin/cleanup, /admin/state")
    logger.info(f"Request deduplication: ENABLED")
    logger.info(f"Project cooldown: {COOLDOWN_MINUTES} minutes")
    
    # Cleanup old entries on startup
    state_manager.cleanup_old_entries()
    
    app.run(host=HOST, port=PORT, debug=False)