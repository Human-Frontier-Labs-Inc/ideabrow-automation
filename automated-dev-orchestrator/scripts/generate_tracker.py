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
                5. Primary application category (e.g., e-commerce, blog, social media, real-time chat, SaaS dashboard, marketplace, etc.)
                
                Output a structured summary focusing on WHAT needs to be built, not HOW.
                Be concise but comprehensive. Identify the MVP scope clearly.
                
                IMPORTANT: Since all projects use Clerk authentication, Supabase database, and Next.js 14+, 
                emphasize the primary use case and application type to help with template selection."""
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
                "content": """You are creating a PROGRESS_TRACKER.md for an AI developer who will implement this project using Next.js.

                <critical_format_requirement>
                The FIRST LINE of your response MUST be EXACTLY in this format:
                # Project: [Replace this with a 2-4 word project name]
                
                DO NOT use generic names. Extract a specific, meaningful name from the requirements.
                Examples of GOOD names: "Task Tracker", "E-Commerce Platform", "Chat Application", "Blog Engine"
                Examples of BAD names: "Project", "Application", "System", "Software"
                </critical_format_requirement>

                <tech_stack>
                ALL projects use this EXACT stack:
                - Framework: Next.js 14+ (App Router)
                - Authentication: Clerk
                - Database: Supabase (PostgreSQL)
                - File Storage: Supabase Storage / S3
                - Payments: Stripe (if needed)
                - Styling: Tailwind CSS
                - Deployment: Vercel
                </tech_stack>
                
                <required_structure>
                # Project: [SPECIFIC NAME HERE]
                
                ## Overview
                [2-3 sentence functional description. What does this app DO for users? Include the primary use case category if relevant: e-commerce, blog, social media, real-time chat, SaaS dashboard, etc.]
                
                ## Tech Stack Requirements
                **IMPORTANT**: Before starting implementation, research current Next.js best practices and conventions as they change frequently.
                - Framework: Next.js 14+ with App Router
                - Auth: Clerk (refer to docs/document-X.md for auth requirements)
                - Database: Supabase
                - Storage: Supabase Storage/S3
                - Payments: Stripe (if applicable)
                
                ## Phase 1: Foundation & Setup
                ### Objectives
                - Set up Next.js project with TypeScript
                - Configure Clerk authentication
                - Initialize Supabase client and database schema
                - Implement base layouts and routing structure
                
                ### Functional Requirements
                - [Reference specific requirements from docs/document-X.md]
                - [User should be able to...]
                - [System should...]
                
                ### Success Criteria
                - [ ] Next.js app runs locally with proper TypeScript config
                - [ ] Clerk auth flow works (sign up, sign in, sign out)
                - [ ] Supabase connected with initial schema deployed
                - [ ] Base routing structure matches requirements in docs/
                
                ## Phase 2: Core Features
                ### Objectives
                - Implement primary user workflows
                - Build main data models and API routes
                - Create essential UI components
                
                ### Functional Requirements
                - [Specific features from docs/document-X.md]
                - [User workflows that must work]
                - [Data operations required]
                
                ### Success Criteria
                - [ ] User can [specific action from requirements]
                - [ ] Data persists correctly in Supabase
                - [ ] API routes handle CRUD operations
                - [ ] UI displays real-time data updates
                
                ## Phase 3: Enhanced Features
                ### Objectives
                - Add secondary features from requirements
                - Implement advanced interactions
                - Enhance user experience
                
                ### Functional Requirements
                - [Additional features from docs/]
                - [Enhanced workflows]
                - [Performance requirements]
                
                ### Success Criteria
                - [ ] [Specific enhanced feature works]
                - [ ] Performance meets requirements
                - [ ] Error handling implemented
                
                ## Phase 4: Integration & Polish
                ### Objectives
                - Integrate third-party services
                - Polish UI/UX
                - Implement responsive design
                
                ### Functional Requirements
                - [Integration requirements from docs/]
                - [UI polish requirements]
                - [Mobile responsiveness needs]
                
                ### Success Criteria
                - [ ] Stripe payments work (if applicable)
                - [ ] Mobile responsive on all screens
                - [ ] Loading states and error boundaries implemented
                - [ ] Accessibility standards met
                
                ## Phase 5: Testing & Deployment
                ### Objectives
                - Comprehensive testing
                - Deploy to Vercel
                - Set up monitoring
                
                ### Functional Requirements
                - All features from docs/ work as specified
                - Performance requirements met
                - Security best practices implemented
                
                ### Success Criteria
                - [ ] All user flows tested and working
                - [ ] Deployed to Vercel successfully
                - [ ] Environment variables configured
                - [ ] Monitoring and error tracking active
                
                ## Implementation Notes
                - Check Next.js documentation for latest App Router patterns
                - Use Server Components where possible for performance
                - Implement proper loading.tsx and error.tsx files
                - Follow Clerk's Next.js integration guide
                - Use Supabase Row Level Security (RLS)
                - Reference docs/ folder for detailed requirements
                
                ## Key User Flows
                [List the main user journeys based on requirements, e.g.:]
                1. User signs up → completes profile → accesses dashboard
                2. [Other critical paths from requirements]
                </required_structure>
                
                <instructions_for_ai_developer>
                IMPORTANT: 
                - NO CODE EXAMPLES in this tracker
                - Reference the docs/ folder for detailed requirements
                - Focus on WHAT functionality to build, not HOW
                - Each phase should reference specific requirements from documentation
                - Success criteria should be testable user actions
                - Ignore compliance/legal sections unless critical to functionality
                - If compliance is critical, add a "Compliance Notes" section at the end
                </instructions_for_ai_developer>

                <critical_guardrails>
                ⚠️ CRITICAL: The structure above contains PLACEHOLDER EXAMPLES in square brackets [ ].
                
                You MUST:
                1. REPLACE every [bracketed placeholder] with ACTUAL content from the provided requirements
                2. NEVER leave generic placeholders like "[Specific features from docs/document-X.md]"
                3. EXTRACT real feature names, user actions, and requirements from the documentation
                4. Reference actual document numbers (e.g., "docs/document-1.md" not "document-X.md")
                5. Create SPECIFIC success criteria based on the actual app functionality
                
                EXAMPLES OF WHAT NOT TO DO:
                ❌ "User can [specific action from requirements]"
                ❌ "[Additional features from docs/]"
                ❌ "refer to docs/document-X.md"
                
                EXAMPLES OF WHAT TO DO:
                ✅ "User can create and manage support tickets with video attachments"
                ✅ "Implement real-time chat system with typing indicators (docs/document-2.md)"
                ✅ "Senior users can schedule video calls with tech support agents"
                
                The placeholders are ONLY to show you the structure. You must fill them with REAL, SPECIFIC content extracted from the actual requirements provided. If you cannot extract specific requirements, you must still create concrete, actionable items based on the project type.
                
                VALIDATION CHECK: Before responding, verify that:
                - Every bullet point contains specific, actionable information
                - No square brackets remain in your response (except checkbox syntax)
                - Document references use actual filenames
                - Success criteria describe real user actions, not placeholders
                </critical_guardrails>
                
                Start your response with "# Project: " followed by a meaningful project name extracted from the actual requirements."""
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