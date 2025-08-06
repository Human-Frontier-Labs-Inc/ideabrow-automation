# Technical Architecture - Anonymous Freedom Blog

## System Design Philosophy
"Privacy by Design, Simplicity by Default"

## Tech Stack

### Frontend
- **Next.js 14** - Server-side rendering for SEO and performance
- **Tailwind CSS** - Minimal, fast styling
- **MDX Editor** - Markdown editing with preview
- **React Markdown** - Safe markdown rendering
- **No Analytics** - Zero tracking scripts

### Backend
- **Next.js API Routes** - Simple, serverless-ready
- **Prisma with SQLite** - Local database, easy to backup
- **Redis** - Rate limiting and temporary edit tokens
- **Sharp** - Image processing and EXIF stripping

### Infrastructure
- **Vercel/Self-hosted** - Easy deployment options
- **Cloudflare** - DDoS protection and CDN
- **Backblaze B2** - Cheap image storage
- **Tor Hidden Service** - Optional .onion address

## Database Schema

### Posts Table
```prisma
model Post {
  id            String   @id @default(cuid())
  content       String   @db.Text
  contentHtml   String   @db.Text // Pre-rendered for performance
  authorName    String   @default("Anonymous")
  category      String?
  tags          String[] // Array of tags
  
  createdAt     DateTime @default(now())
  editToken     String?  // Temporary, expires after 15 min
  editExpiry    DateTime?
  
  viewCount     Int      @default(0)
  flagCount     Int      @default(0)
  isHidden      Boolean  @default(false)
  
  // No IP, no user agent, no tracking
  
  @@index([createdAt(sort: Desc)])
  @@index([category, createdAt(sort: Desc)])
  @@fulltext([content])
}
```

### Flags Table
```prisma
model Flag {
  id        String   @id @default(cuid())
  postId    String
  reason    String   // "spam", "illegal", "personal_info", "other"
  createdAt DateTime @default(now())
  
  // We store a hash of IP + daily salt for rate limiting only
  ipHash    String
  
  @@index([postId])
  @@index([createdAt])
}
```

### RateLimit Table (Redis)
```
Key: rate_limit:{ip_hash}
Value: post_count
TTL: 600 seconds (10 minutes)
```

## API Endpoints

### Public Endpoints
```
GET  /api/posts              - List posts (paginated)
GET  /api/posts/[id]         - Get single post
GET  /api/posts/random       - Random post
POST /api/posts              - Create new post
PUT  /api/posts/[id]         - Edit post (requires token)
POST /api/posts/[id]/flag    - Flag post
GET  /api/search             - Search posts
GET  /api/feed/[category]    - RSS feed
```

### Admin Endpoints (Protected)
```
GET  /api/admin/flags        - Review flagged posts
POST /api/admin/hide/[id]    - Hide/unhide post
GET  /api/admin/stats        - Basic statistics
```

## Security Measures

### Input Sanitization
```typescript
// Sanitize all user input
function sanitizeContent(content: string): string {
  // Remove any potential XSS
  const cleaned = DOMPurify.sanitize(content);
  
  // Strip suspicious patterns
  const noPersonalInfo = cleaned.replace(
    /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g, 
    '[email]'
  );
  
  return noPersonalInfo;
}
```

### Rate Limiting
```typescript
async function checkRateLimit(req: Request): Promise<boolean> {
  const ipHash = hashIP(req.ip + getDailySalt());
  const count = await redis.incr(`rate_limit:${ipHash}`);
  
  if (count === 1) {
    await redis.expire(`rate_limit:${ipHash}`, 600);
  }
  
  return count <= 1; // 1 post per 10 minutes
}
```

### Image Processing
```typescript
async function processImage(buffer: Buffer): Promise<Buffer> {
  return sharp(buffer)
    .rotate() // Auto-rotate based on EXIF
    .withMetadata({
      // Strip all EXIF data
      exif: {},
      icc: {},
      iptc: {},
      xmp: {}
    })
    .resize(1920, 1920, {
      fit: 'inside',
      withoutEnlargement: true
    })
    .jpeg({ quality: 85 })
    .toBuffer();
}
```

## Privacy Implementation

### No Tracking
```typescript
// No Google Analytics
// No Facebook Pixel  
// No Hotjar
// No Sentry error tracking with PII

// Only anonymous error logging
function logError(error: Error) {
  console.error({
    message: error.message,
    stack: error.stack,
    timestamp: new Date().toISOString()
    // No user data, no IP, no session
  });
}
```

### Anonymous Names Generator
```typescript
const adjectives = ['Thoughtful', 'Curious', 'Wandering', 'Mysterious', 'Bold'];
const animals = ['Penguin', 'Octopus', 'Raven', 'Wolf', 'Butterfly'];

function generateAnonName(): string {
  const adj = adjectives[Math.floor(Math.random() * adjectives.length)];
  const animal = animals[Math.floor(Math.random() * animals.length)];
  const num = Math.floor(Math.random() * 9999);
  
  return `${adj} ${animal} #${num}`;
}
```

## Performance Optimizations

### Static Generation
- Homepage pre-rendered every 60 seconds
- Category pages cached for 5 minutes
- Individual posts cached indefinitely

### Database Queries
```typescript
// Efficient pagination
const posts = await prisma.post.findMany({
  where: { isHidden: false },
  orderBy: { createdAt: 'desc' },
  take: 20,
  skip: page * 20,
  select: {
    id: true,
    authorName: true,
    content: true,
    category: true,
    createdAt: true,
    viewCount: true
  }
});
```

### CDN Headers
```typescript
// Aggressive caching for anonymous content
res.setHeader('Cache-Control', 'public, max-age=300, stale-while-revalidate=600');
res.setHeader('X-Robots-Tag', 'index, follow');
```

## Deployment Configuration

### Environment Variables
```env
DATABASE_URL="file:./anon-blog.db"
REDIS_URL="redis://localhost:6379"
IMAGE_STORAGE_URL="https://b2.backblaze.com/bucket"
DAILY_SALT_ROTATION="0 0 * * *"
MAX_POST_LENGTH="10000"
FLAG_THRESHOLD="10"
ADMIN_PASSWORD_HASH="..." # For emergency moderation
```

### Tor Configuration
```nginx
# .onion address configuration
server {
  listen 80;
  server_name xyz123.onion;
  
  # No logs for Tor traffic
  access_log off;
  error_log /dev/null;
  
  location / {
    proxy_pass http://localhost:3000;
    proxy_set_header Host $host;
  }
}
```