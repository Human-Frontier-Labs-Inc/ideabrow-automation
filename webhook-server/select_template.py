#!/usr/bin/env python3
"""
Template Selection Module
Selects the best template based on requirements and hints
"""

import os
import json
from pathlib import Path

def select_template(requirements="", template_hint=None):
    """
    Select the most appropriate template based on requirements
    
    Args:
        requirements (str): Description of project requirements
        template_hint (str): Optional hint about which template to use
    
    Returns:
        dict: Template information with name and full path
    """
    templates_dir = Path("/home/wv3/templates")
    
    # Default template mapping
    templates = {
        "nextjs-clerk-prisma": {
            "keywords": ["nextjs", "next.js", "react", "web app", "full stack", "auth", "database"],
            "description": "Next.js 14+ with Clerk auth and Prisma/SQLite"
        },
        "nextjs-blog": {
            "keywords": ["blog", "content", "markdown", "cms"],
            "description": "Blog template with markdown support"
        },
        "react-dashboard": {
            "keywords": ["dashboard", "admin", "analytics", "charts"],
            "description": "React dashboard with analytics"
        },
        "express-api": {
            "keywords": ["api", "backend", "express", "rest"],
            "description": "Express.js API server"
        }
    }
    
    # If template hint is provided, try to use it first
    if template_hint:
        # Clean the hint
        hint = template_hint.lower().replace("/", "-").replace("_", "-")
        
        # Check if it matches a known template
        for template_name in templates.keys():
            if hint in template_name or template_name in hint:
                template_path = templates_dir / template_name
                if template_path.exists():
                    return {
                        "template": template_name,
                        "full_path": str(template_path),
                        "reason": "template_hint"
                    }
    
    # Score templates based on requirements
    req_lower = requirements.lower()
    best_score = 0
    best_template = "nextjs-clerk-prisma"  # Default fallback
    
    for template_name, template_info in templates.items():
        score = 0
        
        # Check keyword matches
        for keyword in template_info["keywords"]:
            if keyword in req_lower:
                score += 1
        
        # Boost score for explicit mentions
        if template_name.replace("-", " ") in req_lower:
            score += 5
        
        if score > best_score:
            best_score = score
            best_template = template_name
    
    # Verify the selected template exists
    template_path = templates_dir / best_template
    if not template_path.exists():
        # Fallback to first available template
        for template_name in templates.keys():
            fallback_path = templates_dir / template_name
            if fallback_path.exists():
                best_template = template_name
                template_path = fallback_path
                break
        else:
            # No templates found, create a minimal response
            return {
                "template": "minimal",
                "full_path": str(templates_dir / "minimal"),
                "reason": "no_templates_available"
            }
    
    return {
        "template": best_template,
        "full_path": str(template_path),
        "reason": "keyword_match" if best_score > 0 else "default"
    }

if __name__ == "__main__":
    # Test the template selection
    test_cases = [
        ("Build a blog with Next.js", None),
        ("Create a dashboard with analytics", None),
        ("Build an API with Express", None),
        ("Full stack web app with authentication", None),
        ("", "nextjs-blog")
    ]
    
    for requirements, hint in test_cases:
        result = select_template(requirements, hint)
        print(f"Requirements: {requirements}")
        print(f"Hint: {hint}")
        print(f"Selected: {result}")
        print("---")