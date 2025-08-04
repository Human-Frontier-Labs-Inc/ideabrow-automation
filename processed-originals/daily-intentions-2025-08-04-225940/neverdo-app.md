# NeverDo - Stay True to Yourself

## Overview
NeverDo is a simple web application that helps users stay true to themselves by tracking things they always want to do or never want to do, sending daily email reminders with their personalized lists.

## Tagline
"Stay True to Yourself" - A daily reminder of your personal commitments and boundaries.

## Core Features
- User registration and authentication
- Create and manage "Always Do" lists
- Create and manage "Never Do" lists
- Add, edit, and delete items dynamically
- Daily email notifications at user-preferred time
- Simple, clean interface for list management
- Mobile-responsive design

## Technical Requirements
- Next.js 15 with App Router
- TypeScript for type safety
- PostgreSQL database for user data
- Prisma ORM for database management
- Tailwind CSS for styling
- NextAuth for authentication
- Resend or SendGrid for email notifications
- Vercel Cron Jobs for daily email scheduling

## User Flow
1. User signs up with email
2. Creates their "Always Do" and "Never Do" lists
3. Sets preferred notification time
4. Receives daily email with both lists
5. Can update lists anytime through web interface

## Data Model
- Users (email, name, notification_time)
- Lists (user_id, type: 'always' | 'never')
- ListItems (list_id, text, created_at, order)
- NotificationSettings (user_id, enabled, time)

## Success Criteria
- Simple one-page interface
- Email delivery reliability > 99%
- List updates save instantly
- Mobile-friendly design
- Fast page loads < 1 second