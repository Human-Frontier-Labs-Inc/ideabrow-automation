# Automated Development Orchestrator System

## Purpose
Transform project requirements pushed to GitHub into active development environments with AI agents working autonomously in tmux sessions on a remote server.

## Complete Workflow

```
1. Push new project directory to ideabrow-automation repo
   └── projects/{project-name}/requirements/*.md

2. GitHub Actions workflow triggers
   ├── Detects new directory
   ├── Sends docs to LLM API
   ├── Generates PROGRESS_TRACKER.md (phased development plan)
   ├── Creates new GitHub repo: {project-name}-development
   └── Sends webhook to development server

3. Development server receives webhook
   ├── Creates tmux session: {project-name}-dev
   ├── Clones new repo with PROGRESS_TRACKER.md
   ├── Applies boilerplate template
   ├── Starts Claude Code with context
   └── Begins autonomous development
```

## System Components

### GitHub Side
- **Repository**: ideabrow-automation (monitored for new projects)
- **Workflow**: `.github/workflows/project-orchestrator.yml`
- **LLM Processing**: Claude/OpenAI API generates progress tracker
- **Output**: New repo with structured development plan

### Server Side
- **Webhook Receiver**: HTTP endpoint (port 8080)
- **Session Manager**: Automated tmux session creator
- **Template Engine**: Selects from 300+ boilerplates
- **Claude Code Runner**: Initialized with project context

## Data Flow

### Webhook Payload Structure
```json
{
  "project_name": "example-app",
  "repo_url": "https://github.com/org/example-app-development",
  "tracker_url": "https://raw.githubusercontent.com/org/example-app-development/main/PROGRESS_TRACKER.md",
  "requirements_summary": "E-commerce platform with React frontend",
  "template_hint": "react-typescript-commerce",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Tmux Session Layout
```
Session: example-app-dev
┌─────────────────────────┬─────────────────────────┐
│ Pane 1: Claude Code     │ Pane 2: Progress View   │
│ Working directory:      │ Showing:                │
│ ~/projects/example-app  │ PROGRESS_TRACKER.md     │
├─────────────────────────┼─────────────────────────┤
│ Pane 3: Terminal        │ Pane 4: File Browser    │
│ Ready for commands      │ Ranger/tree view        │
└─────────────────────────┴─────────────────────────┘
```

## Critical Success Factors

1. **Zero Human Intervention**: Push to repo → running development session
2. **Session Persistence**: Tmux sessions survive disconnection
3. **Progress Visibility**: Each phase completion commits to GitHub
4. **Template Matching**: Automatic selection based on requirements
5. **Context Preservation**: Claude Code starts with full project understanding

## Example End-to-End Flow

1. Developer pushes directory: `projects/chat-app/requirements/`
2. GitHub Action processes 3 markdown files describing a chat application
3. LLM generates 5-phase PROGRESS_TRACKER.md
4. New repo created: `chat-app-development`
5. Webhook sent to `http://dev-server:8080/create-session`
6. Server creates tmux session `chat-app-dev`
7. Claude Code begins Phase 1: Foundation Setup
8. Commits progress after each phase completion
9. Developer can attach to session anytime: `tmux attach -t chat-app-dev`