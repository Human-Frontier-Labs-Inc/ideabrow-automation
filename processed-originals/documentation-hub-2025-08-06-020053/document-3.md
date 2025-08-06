# UI/UX Design Specifications - Anonymous Freedom Blog

## Design Principles
1. **Brutalist Minimalism** - Function over form
2. **Privacy-First** - No unnecessary elements that could track users
3. **Speed** - Every millisecond counts
4. **Accessibility** - Works for everyone, everywhere

## Visual Design

### Color Palette
```css
:root {
  /* Dark Theme (Default) */
  --bg-primary: #0a0a0a;
  --bg-secondary: #1a1a1a;
  --text-primary: #e0e0e0;
  --text-secondary: #a0a0a0;
  --accent: #00ff88;
  --danger: #ff3366;
  --warning: #ffaa00;
  --border: #333333;
  
  /* Light Theme (Optional) */
  --light-bg-primary: #ffffff;
  --light-bg-secondary: #f5f5f5;
  --light-text-primary: #0a0a0a;
  --light-text-secondary: #666666;
}
```

### Typography
```css
/* System font stack for privacy */
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 
             system-ui, sans-serif;

/* Monospace for posts */
--font-mono: 'Courier New', Courier, monospace;

/* Font sizes */
--text-xs: 0.75rem;
--text-sm: 0.875rem;
--text-base: 1rem;
--text-lg: 1.125rem;
--text-xl: 1.5rem;
--text-2xl: 2rem;
```

## Page Layouts

### Homepage
```
┌─────────────────────────────────────┐
│ [Anonymous Freedom Blog]    [Write] │ <- Minimal header
├─────────────────────────────────────┤
│ Categories: [All][Thoughts][Rants]  │
│            [Stories][Random]        │
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ Curious Raven #4823             │ │
│ │ 2 minutes ago                   │ │
│ │                                 │ │
│ │ "The truth about working from   │ │
│ │  home that nobody talks about..." │ │
│ │                                 │ │
│ │ [Read More] 👁 234              │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Anonymous                       │ │
│ │ 15 minutes ago                  │ │
│ │                                 │ │
│ │ "Why I quit social media and    │ │
│ │  feel more connected than ever" │ │
│ │                                 │ │
│ │ [Read More] 👁 567              │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Write Post Page
```
┌─────────────────────────────────────┐
│ [← Back]          [Post Anonymously]│
├─────────────────────────────────────┤
│ Post as: [Anonymous___] 🎲          │
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │                                 │ │
│ │  Write your thoughts here...    │ │
│ │  Markdown supported.            │ │
│ │                                 │ │
│ │                                 │ │
│ │                                 │ │
│ │                                 │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ Category: [Select ▼]                │
│ Characters: 0/10000                 │
├─────────────────────────────────────┤
│ [Preview] [Clear] [Post Anonymously]│
└─────────────────────────────────────┘
```

### Reading View
```
┌─────────────────────────────────────┐
│ [← Back] [Random Post] [Share] [🚩] │
├─────────────────────────────────────┤
│ Wandering Octopus #7291             │
│ Posted 1 hour ago • Thoughts        │
│ 👁 1,234 views                      │
├─────────────────────────────────────┤
│                                     │
│ Title: On Digital Solitude          │
│                                     │
│ I've been thinking about how we've  │
│ traded real connections for digital │
│ likes. This platform is different - │
│ no followers, no likes, just pure   │
│ expression...                       │
│                                     │
│ [Full post content continues...]    │
│                                     │
└─────────────────────────────────────┘
```

## Component Design

### Post Card Component
```jsx
<article className="border border-gray-800 p-4 mb-4 hover:border-accent transition-colors">
  <header className="mb-2">
    <span className="text-accent">{post.authorName}</span>
    <time className="text-secondary ml-2">{timeAgo(post.createdAt)}</time>
  </header>
  
  <div className="text-primary line-clamp-3 mb-2">
    {post.content}
  </div>
  
  <footer className="flex justify-between text-sm text-secondary">
    <Link href={`/post/${post.id}`} className="hover:text-accent">
      Read More →
    </Link>
    <span>👁 {post.viewCount}</span>
  </footer>
</article>
```

### Write Interface
- Minimal toolbar: Bold, Italic, Link, Quote, Code
- Live preview toggle
- Distraction-free mode (hide everything except editor)
- Auto-save to localStorage (cleared on post)
- Markdown shortcuts (Ctrl+B for bold, etc.)

### Mobile Considerations
- Touch-friendly tap targets (min 44px)
- Swipe gestures for navigation
- Optimized for one-thumb operation
- Minimal data usage (no autoplay, lazy load images)

## Interaction Patterns

### Posting Flow
1. Single "Write" button - always visible
2. Editor opens immediately (no modal)
3. Anonymous name pre-filled
4. One-click random name generation
5. Post button changes to "Posting..." on submit
6. Success: Redirect to post with edit link toast
7. Error: Inline error message, content preserved

### Reading Flow
1. Infinite scroll with clear loading states
2. Click anywhere on card to read
3. Keyboard navigation (J/K for next/prev)
4. Share button copies link (no social widgets)
5. Flag button requires confirmation

### Search Experience
```
[🔍 Search posts...          ]
 
Results update as you type
No search history saved
Results show context snippets
```

## Loading States
```
// Skeleton loader for posts
<div className="animate-pulse">
  <div className="h-4 bg-gray-800 rounded w-3/4 mb-2"></div>
  <div className="h-3 bg-gray-800 rounded w-full mb-1"></div>
  <div className="h-3 bg-gray-800 rounded w-5/6"></div>
</div>
```

## Error States
- "No posts yet. Be the first!" (empty state)
- "Connection lost. Retry?" (network error)
- "Post too long. Maximum 10,000 characters" (validation)
- "Please wait 10 minutes before posting again" (rate limit)

## Accessibility Features
- Full keyboard navigation
- ARIA labels for screen readers
- High contrast mode support
- Reduced motion respects preference
- Focus indicators on all interactive elements
- Skip to content link

## Performance Targets
- First Contentful Paint: < 1s
- Time to Interactive: < 2s
- Lighthouse score: 95+
- Bundle size: < 150KB gzipped
- Works on 2G connections

## Progressive Enhancement
1. **No JS**: Basic reading/posting works
2. **With JS**: Rich editor, real-time preview
3. **Modern browser**: Better transitions, local storage
4. **Fast connection**: Instant search, prefetching

## Special Features

### "Felt Cute, Might Delete Later" Mode
- 24-hour self-destructing posts
- Different UI styling (dashed border)
- Countdown timer shown
- No edit capability

### Night Writer Mode
- Ultra-minimal UI
- Just text editor and post button
- Everything else hidden
- Typewriter sounds (optional)

### Chaos Mode
- Random CSS transforms on elements
- Glitch effects
- Matrix rain background
- April Fools' Day default