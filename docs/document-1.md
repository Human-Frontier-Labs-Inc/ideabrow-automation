# Anonymous Freedom Blog 🎭

## Overview
A completely anonymous blogging platform where anyone can post their thoughts, stories, or rants without creating an account or revealing their identity. Think of it as a digital wall where anyone can leave their mark - no signup, no tracking, just pure expression.

## Core Features

### 1. Zero-Barrier Posting
- No account creation required
- No email verification
- No login process
- Just click "New Post" and start writing
- One-click publishing

### 2. Complete Anonymity
- No IP tracking
- No cookies or fingerprinting
- Random post IDs (not sequential)
- No user profiles or history
- Optional anonymous names (or auto-generated ones like "Anonymous Pangolin #2847")

### 3. Post Features
- Rich text editor with markdown support
- Image uploads (auto-stripped of EXIF data)
- Categories/tags for organization
- Character limit: 10,000 per post
- Edit window: 15 minutes after posting (using temporary edit tokens)
- No delete function (posts are permanent)

### 4. Discovery & Reading
- Chronological feed (newest first)
- Category filtering
- Full-text search
- Random post button
- Popular posts (based on views, not votes)
- RSS feed for each category

### 5. Moderation System
- Community flagging (no account needed)
- Auto-hide posts with 10+ flags pending review
- Word filter for obvious spam/illegal content
- Rate limiting: Max 1 post per IP per 10 minutes
- Captcha after 3 posts in an hour

## User Experience

### Posting Flow
1. Land on homepage, see recent posts
2. Click "Write Something" button
3. Type or paste content
4. Optionally add category tags
5. Optionally choose anonymous name or let system generate one
6. Solve simple captcha
7. Click "Post Anonymously"
8. Get temporary edit link (valid for 15 minutes)

### Reading Flow
1. Browse chronological feed
2. Filter by categories
3. Click post to read full content
4. Share post via permalink
5. Flag inappropriate content if needed

## Content Guidelines (Minimal)
- No illegal content
- No personal information of others
- No spam or advertisements
- Everything else is fair game

## Technical Requirements

### Frontend
- Clean, minimalist design
- Fast loading (under 1 second)
- Mobile-first responsive
- Dark mode by default
- No JavaScript required for basic functionality
- Progressive enhancement for rich editor

### Backend
- Handle high volume (10,000+ posts/day)
- Efficient full-text search
- Automatic content backup
- DDoS protection
- Geographic distribution (CDN)

### Privacy Features
- All connections over HTTPS
- No analytics or tracking scripts
- Images served through proxy
- Tor-friendly
- No external resources (fonts, CDNs for JS/CSS)

## Monetization
- Optional cryptocurrency donations
- No ads, no premium features
- Community-funded infrastructure

## Success Metrics
- Posts per day
- Average reading time
- Geographic diversity of posts
- Uptime percentage
- Time to first byte (performance)