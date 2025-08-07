#!/usr/bin/env python3
"""
Phase Scheduler for Tmux Orchestrator
Handles automated phase progression for development projects
"""

import os
import json
import logging
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

# Import testing manager for Phase 2 integration
try:
    from testing_manager import create_testing_manager
except ImportError:
    # Fallback - create dummy testing manager if not available
    def create_testing_manager():
        return None

logger = logging.getLogger(__name__)

class PhaseScheduler:
    """
    Manages phase-based scheduling for project development
    Each project gets automated phase transitions at configured intervals
    """
    
    def __init__(self, orchestrator_script_path="/home/wv3/.claude/orchestrator"):
        self.orchestrator_path = Path(orchestrator_script_path)
        self.send_message_script = self.orchestrator_path / "send-claude-message.sh"
        self.schedule_script = self.orchestrator_path / "schedule_with_note.sh"
        self.testing_manager = create_testing_manager()
        
        # Phase configuration - easily customizable
        self.phase_config = {
            1: {
                "name": "Template Analysis & Setup",
                "duration_minutes": 15,
                "message": self._get_phase_1_message()
            },
            2: {
                "name": "Core Feature Development", 
                "duration_minutes": 30,
                "message": self._get_phase_2_message()
            },
            3: {
                "name": "Enhanced Features & Integration",
                "duration_minutes": 30, 
                "message": self._get_phase_3_message()
            },
            4: {
                "name": "Polish & Testing",
                "duration_minutes": 20,
                "message": self._get_phase_4_message()
            },
            5: {
                "name": "Final Review & Git Commit",
                "duration_minutes": 15,
                "message": self._get_phase_5_message()
            }
        }
    
    def schedule_all_phases(self, project_name, session_params=None):
        """
        Schedule all phases for a project from the beginning
        This is called after initial orchestrator setup
        """
        try:
            logger.info(f"Scheduling all phases for project: {project_name}")
            
            # Calculate cumulative timing for each phase
            total_minutes = 0
            
            for phase_num, phase_info in self.phase_config.items():
                if phase_num == 1:
                    # Phase 1 is already started, schedule the transition to phase 2
                    total_minutes += phase_info["duration_minutes"]
                    continue
                
                total_minutes += phase_info["duration_minutes"]
                
                # Create the phase transition message
                phase_message = phase_info["message"].format(
                    project_name=project_name,
                    phase_num=phase_num,
                    phase_name=phase_info["name"]
                )
                
                # Schedule this phase using nohup for persistence
                self._schedule_phase_transition(
                    project_name=project_name,
                    phase_num=phase_num,
                    delay_minutes=total_minutes,
                    message=phase_message
                )
                
            logger.info(f"All phases scheduled for {project_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling phases for {project_name}: {e}")
            return False
    
    def _schedule_phase_transition(self, project_name, phase_num, delay_minutes, message):
        """
        Schedule a single phase transition using the orchestrator's scheduling system
        Uses nohup-based scheduling for persistence across process exits
        """
        try:
            target_window = f"{project_name}:0.0"  # Claude Code is in pane 0 of window 0
            
            # Escape the message for shell safety
            import shlex
            escaped_message = shlex.quote(message)
            
            # Create a command that will be executed after the delay
            # Using the send-claude-message.sh script directly
            delayed_command = f"{self.send_message_script} {target_window} {escaped_message}"
            
            # Calculate delay in seconds
            delay_seconds = delay_minutes * 60
            
            # Use nohup with sleep to schedule the message
            # This persists even if the parent process exits
            cmd = f"nohup bash -c 'sleep {delay_seconds} && {delayed_command}' > /dev/null 2>&1 &"
            
            logger.info(f"Scheduling Phase {phase_num} for {project_name} in {delay_minutes} minutes")
            
            # Run the scheduling command
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info(f"Successfully scheduled Phase {phase_num} for {project_name} with nohup")
                
                # Special handling for Phase 2 - testing server
                if phase_num == 2 and self.testing_manager:
                    # Schedule testing server start
                    test_cmd = f"nohup bash -c 'sleep {delay_seconds} && echo \"Starting testing server for {project_name}\"' > /dev/null 2>&1 &"
                    subprocess.run(test_cmd, shell=True)
                    logger.info(f"Scheduled testing server start for Phase 2")
                
            else:
                logger.error(f"Failed to schedule Phase {phase_num} for {project_name}: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error in _schedule_phase_transition: {e}")
    
    
    def _get_phase_1_message(self):
        """Phase 1: Template Analysis & Setup - This is the initial phase"""
        return """PHASE 1 COMPLETE CHECK - AGENT SWARM COORDINATION

🚨 CRITICAL: You have access to /home/wv3/.claude/agents directory with specialized agents!

For Phase 1, you should have spawned multiple agents working in PARALLEL:

1. **researcher agent**: Analyze all original docs in /docs folder
2. **code-analyzer agent**: Deep dive into template structure and existing features  
3. **architect-reviewer agent**: Review architecture and identify integration points
4. **docs-architect agent**: Document findings and create technical overview

EACH AGENT MUST:
- Read the ORIGINAL project documentation in /docs folder
- Understand the complete project vision and requirements
- Work on UNIQUE, non-overlapping tasks
- Report findings back to you for synthesis

PHASE 1 VERIFICATION:
1. Did ALL agents read the original /docs folder?
2. Is development server running with Prisma/SQLite?
3. Do you have a complete understanding of project requirements?
4. Have you documented template features vs. requirements gaps?
5. Are all findings synthesized into a cohesive plan?

REMEMBER: Use agent swarms for parallel processing! Don't work sequentially.

If Phase 1 is complete with full agent coordination, confirm for Phase 2."""
    
    def _get_phase_2_message(self):
        """Phase 2: Core Feature Development"""
        return """🚀 PHASE 2: CORE FEATURE DEVELOPMENT - PARALLEL AGENT SWARM

🚨 SPAWN MULTIPLE SPECIALIZED AGENTS for parallel development!

REQUIRED AGENT DEPLOYMENT:
1. **backend-dev agent**: API endpoints and business logic
2. **frontend-developer agent**: UI components and user flows
3. **database-optimizer agent**: Prisma schema and migrations
4. **test-automator agent**: Test cases for each feature
5. **api-documenter agent**: Document all new endpoints

COORDINATION PROTOCOL:
- Each agent reads /docs folder FIRST to understand requirements
- Agents work on SEPARATE, non-conflicting areas
- Use task-orchestrator to coordinate dependencies
- Regular status checks to prevent conflicts
- Synthesize all work before committing

PHASE 2 OBJECTIVES PER AGENT:
- Backend: Core API endpoints from requirements
- Frontend: Main UI workflows from project docs
- Database: Extend Prisma schema per requirements
- Testing: Create tests for EVERY new feature
- Docs: Update API documentation

CRITICAL RULES:
- All agents MUST read original /docs first
- Use Prisma/SQLite (no external DBs)
- Commit every 30 minutes
- No duplicate work between agents
- Coordinate through you as orchestrator

Deploy your agent swarm NOW and coordinate their parallel work!"""
    
    def _get_phase_3_message(self):
        """Phase 3: Enhanced Features & Integration"""
        return """🔧 PHASE 3: ENHANCED FEATURES & INTEGRATION - ADVANCED SWARM

🚨 DEPLOY SPECIALIZED ENHANCEMENT AGENTS!

REQUIRED PHASE 3 AGENTS:
1. **ui-ux-designer agent**: Polish UI/UX based on /docs requirements
2. **performance-engineer agent**: Optimize all features for speed
3. **integration specialist**: Connect third-party services from docs
4. **security-auditor agent**: Implement security best practices
5. **ml-engineer agent**: Add any AI/ML features from requirements

ADVANCED COORDINATION:
- smart-agent to dynamically spawn sub-agents as needed
- perf-analyzer to identify bottlenecks
- Each agent MUST reference original /docs for features
- Parallel work on non-conflicting enhancements

PHASE 3 ENHANCEMENT TARGETS:
- UI/UX: Implement ALL UI enhancements from project docs
- Performance: Sub-second page loads, optimized queries
- Integrations: External APIs mentioned in requirements
- Security: Auth hardening, input validation, CORS
- Advanced: Real-time features, AI capabilities per docs

CRITICAL INSTRUCTIONS:
- Every agent reads /docs to find enhancement requirements
- Continue using Prisma/SQLite for all data
- Mock external services if no credentials
- Test each enhancement thoroughly
- Coordinate to prevent feature conflicts

Spawn your enhancement swarm and orchestrate advanced features!"""
    
    def _get_phase_4_message(self):
        """Phase 4: Polish & Testing"""
        return """✨ PHASE 4: POLISH & TESTING - QUALITY ASSURANCE SWARM

🚨 DEPLOY COMPREHENSIVE TESTING & POLISH AGENTS!

REQUIRED QA SWARM:
1. **test-automator agent**: E2E tests for ALL features in /docs
2. **security-auditor agent**: Penetration testing and security scan
3. **performance-benchmarker agent**: Load testing and optimization
4. **mobile-developer agent**: Responsive design verification
5. **docs-architect agent**: Complete documentation update

PARALLEL TESTING PROTOCOL:
- Each agent reads /docs to understand ALL features to test
- Create test cases for EVERY requirement in docs
- Run tests simultaneously in different areas
- Report all issues for immediate fixing
- Document test results comprehensively

PHASE 4 COVERAGE REQUIREMENTS:
- Testing: 100% of features mentioned in /docs tested
- Security: OWASP top 10 verification
- Performance: Test with 1000x expected load
- Mobile: Test on 5+ screen sizes
- Docs: README, API docs, deployment guide

QUALITY GATES:
- All tests must pass
- No security vulnerabilities
- Page load < 1 second
- Works on all devices
- Documentation complete

Deploy QA swarm for parallel testing and polishing!"""
    
    def _get_phase_5_message(self):
        """Phase 5: Final Review & Deployment"""
        return """🏁 PHASE 5: FINAL REVIEW & GIT COMMIT - DEPLOYMENT SWARM

🚨 FINAL SWARM DEPLOYMENT FOR REVIEW & COMMIT!

REQUIRED FINAL AGENTS:
1. **code-reviewer agent**: Final review against /docs requirements
2. **architect-reviewer agent**: Verify all architecture decisions
3. **docs-architect agent**: Ensure README matches implementation
4. **git specialist**: Prepare comprehensive commit message
5. **deployment-engineer agent**: Verify deployment readiness

FINAL VERIFICATION PROTOCOL:
- Code Review: Check EVERY requirement from /docs is implemented
- Architecture: Verify patterns match project documentation
- Documentation: README has complete setup/usage instructions
- Git: Prepare detailed commit summarizing ALL features
- Deployment: Ensure production readiness

GIT COMMIT AND PUSH REQUIREMENTS:
1. Review ALL original /docs to list implemented features
2. Stage all changes: git add -A
3. Commit message must reference features from docs:
   "Implement [Project Name]: [list ALL major features from docs]
   
   Features implemented from requirements:
   - [Feature 1 from docs]
   - [Feature 2 from docs]
   - [Feature 3 from docs]
   
   Tech: Next.js 14, Prisma/SQLite, Clerk auth"
4. Push to GitHub: git push origin main
5. THIS IS AUTOMATED - You MUST push the code now!

FINAL CHECKLIST:
- ✅ All features from /docs implemented?
- ✅ All tests passing?
- ✅ Documentation complete?
- ✅ Code reviewed by agents?
- ✅ Ready for production?

Deploy final swarm for comprehensive review and commit!"""
    
    def get_phase_status(self, project_name):
        """
        Get the current phase status for a project
        This could be enhanced to track actual progress
        """
        # For now, we calculate based on time elapsed
        # In the future, this could check actual progress markers
        return {"phase": "calculated", "status": "estimated"}
    
    def reschedule_phase(self, project_name, phase_num, new_delay_minutes):
        """
        Reschedule a specific phase (for manual adjustments)
        """
        try:
            if phase_num not in self.phase_config:
                logger.error(f"Invalid phase number: {phase_num}")
                return False
            
            phase_info = self.phase_config[phase_num]
            message = phase_info["message"].format(
                project_name=project_name,
                phase_num=phase_num,
                phase_name=phase_info["name"]
            )
            
            self._schedule_phase_transition(
                project_name=project_name,
                phase_num=phase_num,
                delay_minutes=new_delay_minutes,
                message=message
            )
            
            logger.info(f"Rescheduled Phase {phase_num} for {project_name} in {new_delay_minutes} minutes")
            return True
            
        except Exception as e:
            logger.error(f"Error rescheduling phase: {e}")
            return False

def create_phase_scheduler():
    """Factory function to create a phase scheduler instance"""
    return PhaseScheduler()

if __name__ == "__main__":
    # Test the phase scheduler
    scheduler = PhaseScheduler()
    test_project = "test-project"
    
    print(f"Testing phase scheduler for project: {test_project}")
    success = scheduler.schedule_all_phases(test_project)
    print(f"Scheduling result: {'Success' if success else 'Failed'}")