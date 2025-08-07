#!/usr/bin/env python3
"""
TEMPLATE-AWARE Progress Tracker Generator using OpenRouter API
This version emphasizes analyzing and extending templates rather than building from scratch
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
                
                IMPORTANT: A pre-built template will be used that already includes Next.js 14+, authentication, 
                database setup, and UI components. Focus on the UNIQUE features this project needs."""
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
                "content": """Create a phased development plan with exactly 5 phases.
                
                CRITICAL: The project will use a PRE-BUILT TEMPLATE that already includes:
                - Next.js 14+ setup with TypeScript
                - Authentication (Clerk or similar) 
                - Database connections (Prisma/Supabase)
                - Basic UI components and layouts
                - Routing structure
                - Security and best practices
                
                Therefore:
                Phase 1: Template Analysis & Adaptation (NOT setup from scratch!)
                - Analyze what the template provides
                - Map template features to requirements
                - Identify gaps and needed modifications
                - Plan how to extend existing components
                
                Phase 2: Core Features (Extending template functionality)
                Phase 3: Enhanced Features (Additional custom features)
                Phase 4: Integration & Polish (Third-party services, UI refinement)
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
    
    # Try multiple patterns to find the project name
    patterns = [
        r'^#\s+Project:\s+(.+)$',  # # Project: Name
        r'^Project:\s+(.+)$',       # Project: Name (without #)
        r'^##\s+Project:\s+(.+)$',  # ## Project: Name
        r'^#\s+(.+?)\s*(?:Project|App|Application|System|Platform|Dashboard|Hub|Generator|Manager|Tracker)(?:\s|$)',  # # Name Project/App/etc
    ]
    
    for pattern in patterns:
        match = re.search(pattern, tracker_content, re.MULTILINE | re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean up common prefixes/suffixes
            name = re.sub(r'^(AI-Powered|Smart|Intelligent|Advanced|Professional)\s+', '', name, flags=re.IGNORECASE)
            # Convert to valid repo name (lowercase, replace spaces with hyphens)
            name = re.sub(r'[^a-zA-Z0-9-]', '-', name.lower())
            name = re.sub(r'-+', '-', name).strip('-')
            if name and name != "unnamed" and len(name) > 2:
                return name
    
    # Fallback: try to find any heading that looks like a project name
    heading_match = re.search(r'^#\s+([A-Z][^#\n]{3,50})$', tracker_content, re.MULTILINE)
    if heading_match:
        name = heading_match.group(1).strip()
        # Skip generic headings
        if name.lower() not in ['overview', 'introduction', 'description', 'summary', 'template']:
            name = re.sub(r'[^a-zA-Z0-9-]', '-', name.lower())
            name = re.sub(r'-+', '-', name).strip('-')
            if name and len(name) > 2:
                return name
    
    return "unnamed-project"

def format_progress_tracker(client: OpenAI, project_name: str, plan: str, analysis: str) -> str:
    """Format the final progress tracker document"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """You are creating a PROGRESS_TRACKER.md for an AI developer who will implement this project by EXTENDING A PRE-BUILT TEMPLATE.

                <critical_context>
                THE PROJECT USES A PRE-BUILT TEMPLATE THAT ALREADY INCLUDES:
                - Next.js 14+ with App Router fully configured
                - Authentication system (Clerk/Auth.js) already integrated
                - Database (Prisma/Supabase) already connected with base schema
                - UI components library (shadcn/ui or similar) installed
                - Tailwind CSS configured
                - Basic layouts and routing structure
                - Security best practices implemented
                - Environment variables configured
                
                THE AI DEVELOPER SHOULD NOT REBUILD THESE FROM SCRATCH!
                </critical_context>

                <critical_format_requirement>
                The FIRST LINE of your response MUST be EXACTLY in this format:
                # Project: [Replace this with a 2-4 word project name]
                
                DO NOT use generic names. Extract a specific, meaningful name from the requirements.
                Examples of GOOD names: "Task Tracker", "E-Commerce Platform", "Chat Application", "Blog Engine"
                Examples of BAD names: "Project", "Application", "System", "Software"
                </critical_format_requirement>

                <tech_stack_note>
                The template will determine the exact tech stack. Common patterns:
                - If template uses Clerk → use Clerk's built-in components
                - If template uses Prisma → use Prisma (not Supabase ORM)
                - If template uses shadcn/ui → use those components
                - Work WITH the template's choices, not against them
                </tech_stack_note>
                
                <required_structure>
                # Project: [SPECIFIC NAME HERE]
                
                ## Overview
                [2-3 sentence functional description. What does this app DO for users? Include the primary use case category if relevant: e-commerce, blog, social media, real-time chat, SaaS dashboard, etc.]
                
                ## Template Analysis Requirements
                **CRITICAL**: Before implementing ANY features, thoroughly analyze the provided template.
                The template already includes authentication, database, and core infrastructure.
                Focus on understanding and extending what's already there.
                
                ## Phase 1: Template Analysis & Adaptation
                ### Objectives
                - Run the template and document all existing functionality
                - Map template features to project requirements
                - Identify which existing components can be reused
                - Plan modifications to existing components
                - Document gaps that need new development
                
                ### Tasks
                - [ ] Run `npm install && npm run dev` and explore all template features
                - [ ] Document authentication flow (already implemented by template)
                - [ ] Review database schema and plan extensions (not replacements)
                - [ ] Inventory all UI components and their capabilities
                - [ ] Map existing routes to required features
                - [ ] Create adaptation plan documenting what to modify vs build new
                
                ### Success Criteria
                - [ ] Complete template feature inventory documented
                - [ ] Existing components mapped to requirements
                - [ ] Database extension plan created (keeping existing schema)
                - [ ] UI component reuse strategy documented
                - [ ] Gap analysis complete (what's missing from template)
                
                ## Phase 2: Core Features (Extending Template)
                ### Objectives
                - Extend existing database schema for project-specific needs
                - Modify template components for core functionality
                - Build new features that leverage template infrastructure
                - Implement primary user workflows using existing auth
                
                ### Functional Requirements
                - [Specific features that extend template capabilities]
                - [User workflows building on template's auth system]
                - [Data models that extend template's base schema]
                
                ### Success Criteria
                - [ ] Core features work within template's architecture
                - [ ] Database extensions compatible with template schema
                - [ ] Authentication flow unchanged (using template's system)
                - [ ] New features integrate seamlessly with template
                
                ## Phase 3: Enhanced Features
                ### Objectives
                - Add project-specific advanced features
                - Enhance UX beyond template defaults
                - Implement custom business logic
                
                ### Functional Requirements
                - [Project-specific features not in template]
                - [Custom workflows unique to this project]
                - [Advanced interactions beyond template scope]
                
                ### Success Criteria
                - [ ] Enhanced features maintain template's patterns
                - [ ] Performance remains optimal
                - [ ] User experience improvements measurable
                
                ## Phase 4: Integration & Polish
                ### Objectives
                - Integrate any additional third-party services
                - Polish UI while maintaining template's design system
                - Optimize performance and user experience
                
                ### Functional Requirements
                - [Additional integrations beyond template]
                - [UI customizations respecting template's system]
                - [Performance optimizations needed]
                
                ### Success Criteria
                - [ ] Integrations work smoothly
                - [ ] UI maintains consistency with template
                - [ ] Performance metrics meet targets
                - [ ] Responsive design works across devices
                
                ## Phase 5: Testing & Deployment
                ### Objectives
                - Test all custom features thoroughly
                - Ensure template features still work correctly
                - Deploy using template's deployment configuration
                
                ### Functional Requirements
                - All custom features work as specified
                - Template functionality remains intact
                - Security best practices maintained
                
                ### Success Criteria
                - [ ] All user flows tested end-to-end
                - [ ] No regressions in template functionality
                - [ ] Deployed successfully using template's setup
                - [ ] Monitoring and error tracking configured
                
                ## Implementation Notes
                - DO NOT rebuild authentication - use template's existing system
                - DO NOT create new database connections - extend existing schema
                - DO NOT replace UI component library - use what template provides
                - DO leverage template's existing patterns and conventions
                - DO read template's documentation before making changes
                
                ## Key Principles
                1. **Extend, Don't Replace**: Work with template's existing systems
                2. **Reuse Components**: Prefer modifying existing components over creating new ones
                3. **Maintain Patterns**: Follow template's established patterns
                4. **Respect Architecture**: Don't fight the template's architectural decisions
                </required_structure>
                
                <instructions_for_ai_developer>
                IMPORTANT: 
                - Phase 1 is ALWAYS about understanding the template first
                - Never plan to rebuild what the template provides
                - Reference template documentation when available
                - Focus on extending and customizing, not recreating
                - If template uses Clerk, use Clerk's components (not custom auth pages)
                - If template uses Prisma, use Prisma (not raw SQL or different ORM)
                </instructions_for_ai_developer>

                <critical_guardrails>
                You MUST fill in all placeholders with SPECIFIC content from the requirements.
                But remember: Phase 1 should ALWAYS be about analyzing the template first,
                not building from scratch. The template already has auth, database, and UI.
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
    print("\nStarting TEMPLATE-AWARE generation pipeline...")
    
    client = get_client()
    
    # Step 1: Analyze requirements
    print("Step 1: Analyzing requirements (with template context)...")
    analysis = analyze_requirements(client, requirements)
    
    # Step 2: Create phased plan
    print("Step 2: Creating phased development plan (template-first approach)...")
    plan = create_phased_plan(client, analysis)
    
    # Step 3: Format tracker
    print("Step 3: Formatting progress tracker (emphasizing template extension)...")
    tracker = format_progress_tracker(client, project_name, plan, analysis)
    
    return tracker

async def main():
    parser = argparse.ArgumentParser(description='Generate TEMPLATE-AWARE progress tracker from requirements')
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
    print("NOTE: This is the TEMPLATE-AWARE version that emphasizes extending templates, not building from scratch!")
    
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
        
        print(f"\n✓ TEMPLATE-AWARE Progress tracker generated: {output_path}")
        print(f"  Project: {project_name}")
        print(f"  Size: {len(tracker_content)} characters")
        print(f"  Approach: Template-first (analyze, extend, customize)")
        
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