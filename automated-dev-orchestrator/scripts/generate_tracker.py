#!/usr/bin/env python3
"""
Progress Tracker Generator using OpenRouter API
Processes project requirements and generates a phased development plan
"""

import os
import sys
import argparse
from pathlib import Path
from openai import OpenAI
from typing import List

# Model configuration
MODEL = "z-ai/glm-4.5"

def get_client():
    """Initialize OpenRouter client"""
    api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY or OPENAI_API_KEY environment variable not set")
    
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

def analyze_requirements(client: OpenAI, requirements: str) -> str:
    """Analyze requirements and extract key information"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """You are a requirements analyst. Analyze the provided project documentation and extract:
                1. Core functionality requirements
                2. User stories and primary workflows
                3. Technical constraints and dependencies
                4. Success criteria and key metrics
                
                Output a structured summary focusing on WHAT needs to be built, not HOW.
                Be concise but comprehensive. Identify the MVP scope clearly."""
            },
            {
                "role": "user",
                "content": requirements
            }
        ],
        extra_headers={
            "HTTP-Referer": "https://github.com/Human-Frontier-Labs-Inc/ideabrow-automation",
            "X-Title": "Ideabrow Automation",
        }
    )
    return response.choices[0].message.content

def create_phased_plan(client: OpenAI, analysis: str) -> str:
    """Create a phased development plan"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system", 
                "content": """Create a phased development plan with exactly 5 phases:
                
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
                Each phase should be independently testable and deployable."""
            },
            {
                "role": "user",
                "content": f"Based on this analysis, create a phased development plan:\n\n{analysis}"
            }
        ],
        extra_headers={
            "HTTP-Referer": "https://github.com/Human-Frontier-Labs-Inc/ideabrow-automation",
            "X-Title": "Ideabrow Automation",
        }
    )
    return response.choices[0].message.content

def extract_project_name(tracker_content: str) -> str:
    """Extract project name from the generated tracker"""
    import re
    # Look for "# Project: [Name]" pattern
    match = re.search(r'^#\s+Project:\s+(.+)$', tracker_content, re.MULTILINE)
    if match:
        name = match.group(1).strip()
        # Convert to valid repo name (lowercase, replace spaces with hyphens)
        name = re.sub(r'[^a-zA-Z0-9-]', '-', name.lower())
        name = re.sub(r'-+', '-', name).strip('-')
        return name
    return "unnamed-project"

def format_progress_tracker(client: OpenAI, project_name: str, plan: str, analysis: str) -> str:
    """Format the final progress tracker document"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """Create a PROGRESS_TRACKER.md document with this exact structure:
                
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
                Include practical, measurable success criteria."""
            },
            {
                "role": "user",
                "content": f"Project: {project_name}\n\nPlan:\n{plan}\n\nAnalysis:\n{analysis}"
            }
        ],
        extra_headers={
            "HTTP-Referer": "https://github.com/Human-Frontier-Labs-Inc/ideabrow-automation",
            "X-Title": "Ideabrow Automation",
        }
    )
    return response.choices[0].message.content

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

async def generate_progress_tracker(requirements: str, project_name: str) -> str:
    """Generate progress tracker using sequential API calls"""
    print("\nStarting generation pipeline...")
    
    client = get_client()
    
    # Step 1: Analyze requirements
    print("Step 1: Analyzing requirements...")
    analysis = analyze_requirements(client, requirements)
    
    # Step 2: Create phased plan
    print("Step 2: Creating phased development plan...")
    plan = create_phased_plan(client, analysis)
    
    # Step 3: Format tracker
    print("Step 3: Formatting progress tracker...")
    tracker = format_progress_tracker(client, project_name, plan, analysis)
    
    return tracker

async def main():
    parser = argparse.ArgumentParser(description='Generate progress tracker from requirements')
    parser.add_argument('--project-path', type=str, required=True,
                       help='Path to project requirements directory')
    parser.add_argument('--output', type=str, default='PROGRESS_TRACKER.md',
                       help='Output file name (default: PROGRESS_TRACKER.md)')
    parser.add_argument('--project-name', type=str,
                       help='Project name (extracted from path if not provided)')
    parser.add_argument('--extract-project-name', action='store_true',
                       help='Extract and output project name from generated tracker')
    
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
        tracker_content = await generate_progress_tracker(requirements, project_name)
        
        # Save to file
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            f.write(tracker_content)
        
        # Extract project name if requested
        if args.extract_project_name:
            extracted_name = extract_project_name(tracker_content)
            print(f"PROJECT_NAME:{extracted_name}")
        
        print(f"\n✓ Progress tracker generated: {output_path}")
        print(f"  Project: {project_name}")
        print(f"  Size: {len(tracker_content)} characters")
        
    except Exception as e:
        print(f"Error generating tracker: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    
    # Ensure API key is set
    if not os.getenv('OPENROUTER_API_KEY') and not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENROUTER_API_KEY or OPENAI_API_KEY environment variable not set")
        print("Set your OpenRouter API key: export OPENROUTER_API_KEY=sk-or-...")
        sys.exit(1)
    
    asyncio.run(main())