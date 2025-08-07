#!/usr/bin/env python3
"""
Enhanced Template Selection Module
Selects from ALL available templates (300+) based on requirements
"""

import os
import json
import random
from pathlib import Path

def load_all_templates():
    """Load all available templates from index.json and directories"""
    templates_dir = Path("/home/wv3/templates")
    templates = {}
    
    # Try to load from index.json first
    index_file = templates_dir / "index.json"
    if index_file.exists():
        with open(index_file) as f:
            data = json.load(f)
            for template in data.get("templates", []):
                name = template.get("name", "")
                path = template.get("path", "")
                if name and path and Path(path).exists():
                    templates[name] = {
                        "path": path,
                        "description": template.get("description", ""),
                        "auth": "Clerk" if "clerk" in name.lower() else "Clerk",  # Always default to Clerk
                        "database": "Prisma" if "prisma" in name.lower() else "Prisma/SQLite",
                        "ui": "shadcn/ui" if "shadcn" in name.lower() else "Tailwind CSS",
                        "framework": template.get("framework", "Next.js")
                    }
    
    # Add modern-saas templates (these are our best Clerk-based templates)
    modern_saas_dir = templates_dir / "modern-saas"
    if modern_saas_dir.exists():
        for template_dir in modern_saas_dir.iterdir():
            if template_dir.is_dir():
                name = f"modern-saas/{template_dir.name}"
                templates[name] = {
                    "path": str(template_dir),
                    "description": f"Modern SaaS template with Clerk auth - {template_dir.name}",
                    "auth": "Clerk",  # ALL modern-saas templates use Clerk
                    "database": "Prisma/SQLite",
                    "ui": "shadcn/ui",
                    "framework": "Next.js 14+"
                }
    
    # Add other category templates
    for category in ["clerk-auth", "full-stack", "social-media", "crm-dashboards", "realtime"]:
        category_dir = templates_dir / category
        if category_dir.exists():
            for template_dir in category_dir.iterdir():
                if template_dir.is_dir():
                    name = f"{category}/{template_dir.name}"
                    templates[name] = {
                        "path": str(template_dir),
                        "description": f"{category} template - {template_dir.name}",
                        "auth": "Clerk" if "clerk" in category else "Clerk",  # Default to Clerk
                        "database": "Prisma/SQLite",
                        "ui": "shadcn/ui",
                        "framework": "Next.js 14+"
                    }
    
    return templates

def score_template(template_info, requirements, project_type=None):
    """Score a template based on requirements match"""
    score = 0
    req_lower = requirements.lower()
    
    # Keywords that boost score
    keywords = {
        "saas": ["saas", "subscription", "billing", "stripe", "payment"],
        "blog": ["blog", "content", "markdown", "cms", "posts", "articles"],
        "ecommerce": ["shop", "store", "product", "cart", "checkout", "commerce"],
        "dashboard": ["dashboard", "admin", "analytics", "charts", "metrics"],
        "social": ["social", "chat", "messaging", "feed", "friends", "posts"],
        "crm": ["crm", "customer", "sales", "leads", "contacts"],
        "realtime": ["realtime", "live", "websocket", "chat", "collaborative"],
        "marketplace": ["marketplace", "vendor", "multi-vendor", "sellers"],
        "project": ["project", "task", "kanban", "team", "management"],
        "ai": ["ai", "ml", "gpt", "llm", "generation", "intelligent"]
    }
    
    # Check for keyword matches
    for category, words in keywords.items():
        for word in words:
            if word in req_lower:
                score += 2
                if category in template_info.get("path", "").lower():
                    score += 5  # Bonus if template category matches
    
    # Always prefer modern-saas templates with Clerk
    if "modern-saas" in template_info.get("path", ""):
        score += 10  # Strong preference for modern-saas
    
    # Prefer Clerk auth templates
    if template_info.get("auth") == "Clerk":
        score += 5
    
    # Check description match
    desc_lower = template_info.get("description", "").lower()
    for word in req_lower.split():
        if len(word) > 3 and word in desc_lower:
            score += 1
    
    return score

def select_template(requirements="", template_hint=None):
    """
    Select the most appropriate template from ALL available templates
    
    Args:
        requirements (str): Description of project requirements
        template_hint (str): Optional hint about which template to use
    
    Returns:
        dict: Template information with name, path, and tech stack
    """
    templates = load_all_templates()
    
    if not templates:
        # Fallback if no templates found
        return {
            "template": "modern-saas/nextjs-saas-clerk",
            "full_path": "/home/wv3/templates/modern-saas/nextjs-saas-clerk",
            "auth": "Clerk",
            "database": "Prisma/SQLite",
            "ui": "shadcn/ui",
            "reason": "default_fallback"
        }
    
    # If template hint is provided, try to find exact match
    if template_hint:
        hint_clean = template_hint.lower().replace("_", "-")
        
        # Direct match
        if hint_clean in templates:
            template = templates[hint_clean]
            return {
                "template": hint_clean,
                "full_path": template["path"],
                "auth": template["auth"],
                "database": template["database"],
                "ui": template["ui"],
                "reason": "exact_hint_match"
            }
        
        # Partial match
        for name, template in templates.items():
            if hint_clean in name or name in hint_clean:
                return {
                    "template": name,
                    "full_path": template["path"],
                    "auth": template["auth"],
                    "database": template["database"],
                    "ui": template["ui"],
                    "reason": "partial_hint_match"
                }
    
    # Score all templates
    scored_templates = []
    for name, template in templates.items():
        score = score_template(template, requirements)
        scored_templates.append((score, name, template))
    
    # Sort by score (highest first)
    scored_templates.sort(key=lambda x: x[0], reverse=True)
    
    # Get top templates with similar scores (within 2 points of best)
    if scored_templates:
        best_score = scored_templates[0][0]
        top_templates = [t for t in scored_templates if t[0] >= best_score - 2]
        
        # Randomly select from top templates for variety
        selected = random.choice(top_templates) if top_templates else scored_templates[0]
        
        return {
            "template": selected[1],
            "full_path": selected[2]["path"],
            "auth": selected[2]["auth"],
            "database": selected[2]["database"],
            "ui": selected[2]["ui"],
            "reason": f"scored_{selected[0]}",
            "total_templates_considered": len(templates)
        }
    
    # Ultimate fallback
    return {
        "template": "modern-saas/nextjs-saas-clerk",
        "full_path": "/home/wv3/templates/modern-saas/nextjs-saas-clerk",
        "auth": "Clerk",
        "database": "Prisma/SQLite",
        "ui": "shadcn/ui",
        "reason": "final_fallback"
    }

if __name__ == "__main__":
    # Test the enhanced template selection
    test_requirements = [
        "Build a project management app with kanban boards",
        "Create a blog with markdown support",
        "E-commerce marketplace with multiple vendors",
        "Real-time chat application",
        "SaaS dashboard with billing"
    ]
    
    print("Enhanced Template Selection Test")
    print("=" * 60)
    
    templates = load_all_templates()
    print(f"Total templates available: {len(templates)}")
    print()
    
    for req in test_requirements:
        result = select_template(req)
        print(f"Requirement: {req}")
        print(f"Selected: {result['template']}")
        print(f"Auth: {result['auth']}")
        print(f"Database: {result['database']}")
        print(f"Reason: {result['reason']}")
        print("-" * 40)