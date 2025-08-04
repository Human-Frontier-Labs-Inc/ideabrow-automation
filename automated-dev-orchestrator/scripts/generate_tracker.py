#!/usr/bin/env python3
"""
Progress Tracker Generator using OpenAI Agents SDK with OpenRouter
Processes project requirements and generates a phased development plan
"""

import asyncio
import os
import sys
import argparse
from pathlib import Path
from agents import Agent, Runner
from typing import List

# Configure OpenRouter endpoint
os.environ['OPENAI_BASE_URL'] = os.getenv('OPENAI_BASE_URL', 'https://openrouter.ai/api/v1')

# Model configuration
MODEL = "z-ai/glm-4-5"  # More reliable than glm-4.5 for complex tasks

# Agent 1: Requirements Analyzer
requirements_analyzer = Agent(
    name="Requirements Analyzer",
    model=MODEL,
    instructions="""
    Analyze the provided project documentation and extract:
    1. Core functionality requirements
    2. User stories and primary workflows
    3. Technical constraints and dependencies
    4. Success criteria and key metrics
    
    Output a structured summary focusing on WHAT needs to be built, not HOW.
    Be concise but comprehensive. Identify the MVP scope clearly.
    """
)

# Agent 2: Phase Planner
phase_planner = Agent(
    name="Phase Planner",
    model=MODEL,
    instructions="""
    Create a phased development plan with exactly 5 phases:
    
    Phase 1: Foundation (Setup, core structure, basic scaffolding)
    Phase 2: Core Features (Primary functionality, MVP features)
    Phase 3: Enhanced Features (Secondary features, improvements)
    Phase 4: Integration & Polish (Third-party integrations, UI polish)
    Phase 5: Testing & Deployment (Comprehensive testing, deployment prep)
    
    For each phase:
    - Clear deliverables (what will exist after this phase)
    - Specific acceptance criteria (how to verify completion)
    - User-visible outcomes (what users can do)
    
    NO CODE IMPLEMENTATION DETAILS. Focus on functional descriptions.
    Each phase should be independently testable and deployable.
    """
)

# Agent 3: Progress Tracker Formatter
tracker_formatter = Agent(
    name="Tracker Formatter",
    model=MODEL,
    instructions="""
    Create a PROGRESS_TRACKER.md document with this exact structure:
    
    # Project: [Name]
    
    ## Overview
    [2-3 sentence project description]
    
    ## Phase 1: Foundation
    ### Objectives
    - [Bullet points]
    
    ### Deliverables
    - [Specific items]
    
    ### Success Criteria
    - [ ] [Checkable items]
    
    ## Phase 2: Core Features
    [Same structure]
    
    ## Phase 3: Enhanced Features
    [Same structure]
    
    ## Phase 4: Integration & Polish
    [Same structure]
    
    ## Phase 5: Testing & Deployment
    [Same structure]
    
    ## Technical Notes
    - [Key technical decisions to be made]
    - [Important constraints]
    
    ## User Flows
    [Brief description of main user journeys]
    
    Make it scannable by AI agents. Use consistent markdown formatting.
    Include practical, measurable success criteria.
    """
)

# Orchestrator Agent
orchestrator = Agent(
    name="Project Orchestrator",
    model=MODEL,
    instructions="""
    You coordinate the analysis and planning of software projects.
    Process requirements through the specialist agents in sequence:
    1. First analyze requirements
    2. Then create phased plan
    3. Finally format as progress tracker
    
    Ensure the final output is practical and actionable for AI developers.
    """,
    handoffs=[requirements_analyzer, phase_planner, tracker_formatter]
)


async def read_requirements(project_path: Path) -> str:
    """Read all markdown files from the requirements directory"""
    requirements = []
    
    # Find all .md files in the project path
    md_files = list(project_path.glob("**/*.md"))
    
    if not md_files:
        raise ValueError(f"No markdown files found in {project_path}")
    
    print(f"Found {len(md_files)} requirement files:")
    for md_file in md_files:
        print(f"  - {md_file.name}")
        with open(md_file, 'r') as f:
            content = f.read()
            requirements.append(f"## File: {md_file.name}\n\n{content}")
    
    return "\n\n---\n\n".join(requirements)


async def generate_progress_tracker(requirements: str) -> str:
    """Generate progress tracker using agent pipeline"""
    print("\nStarting agent pipeline...")
    
    prompt = f"""
    Process these project requirements and create a comprehensive progress tracker.
    The tracker should guide an AI developer through building this application.
    
    REQUIREMENTS:
    
    {requirements}
    
    Create a phased development plan that is clear, actionable, and measurable.
    """
    
    result = await Runner.run(orchestrator, prompt)
    return result.final_output


async def main():
    parser = argparse.ArgumentParser(description='Generate progress tracker from requirements')
    parser.add_argument('--project-path', type=str, required=True,
                       help='Path to project requirements directory')
    parser.add_argument('--output', type=str, default='PROGRESS_TRACKER.md',
                       help='Output file name (default: PROGRESS_TRACKER.md)')
    parser.add_argument('--project-name', type=str,
                       help='Project name (extracted from path if not provided)')
    
    args = parser.parse_args()
    
    # Validate project path
    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Error: Project path {project_path} does not exist")
        sys.exit(1)
    
    # Extract project name if not provided
    project_name = args.project_name or project_path.name
    print(f"Processing project: {project_name}")
    
    try:
        # Read requirements
        requirements = await read_requirements(project_path)
        
        # Generate tracker
        tracker_content = await generate_progress_tracker(requirements)
        
        # Save to file
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            f.write(tracker_content)
        
        print(f"\n✓ Progress tracker generated: {output_path}")
        print(f"  Project: {project_name}")
        print(f"  Size: {len(tracker_content)} characters")
        
    except Exception as e:
        print(f"Error generating tracker: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Ensure API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Set your OpenRouter API key: export OPENAI_API_KEY=sk-or-...")
        sys.exit(1)
    
    asyncio.run(main())