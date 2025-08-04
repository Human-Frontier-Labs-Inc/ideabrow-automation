# Real-Time Chat Application v3 - FINAL TEST

## Overview
Build a real-time chat application with instant messaging, presence indicators, and file sharing capabilities.

## Core Requirements

### Authentication & User Management
- User registration with email verification
- OAuth integration (Google, GitHub)
- User profiles with avatars
- Online/offline status tracking

### Chat Features
- Real-time messaging with WebSocket
- Direct messages (1-on-1 chats)
- Group chat rooms
- Message history and search
- Typing indicators
- Read receipts
- File and image sharing
- Emoji reactions

### Room Management
- Create public and private rooms
- Invite users to rooms
- Room moderation (kick, ban)
- Room settings and permissions

### Notifications
- Desktop notifications
- Sound alerts
- Unread message badges
- Email notifications for offline users

## Technical Stack

### Frontend
- Next.js 14 with App Router
- TypeScript for type safety
- Tailwind CSS for styling
- Socket.io-client for WebSocket
- React Query for data fetching

### Backend
- Node.js with Express
- Socket.io for real-time communication
- PostgreSQL with Prisma ORM
- Redis for session management
- S3 for file storage

### Infrastructure
- Docker containers
- Kubernetes for scaling
- Nginx reverse proxy
- SSL/TLS encryption

## Success Metrics
- Messages delivered in < 100ms
- Support 10,000 concurrent users
- 99.9% uptime
- Mobile responsive design