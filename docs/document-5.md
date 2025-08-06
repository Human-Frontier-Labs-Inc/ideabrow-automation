# Privacy & Security Deep Dive - Anonymous Freedom Blog

## Privacy Architecture

### Core Privacy Principles
1. **Data Minimization** - Collect nothing unnecessary
2. **Privacy by Default** - Anonymous unless user chooses otherwise
3. **Transparency** - Clear about what little we store
4. **User Control** - Edit window, no permanent accounts
5. **Security First** - Protect what little data exists

## What We DON'T Store

### Never Collected
- IP addresses (only hashed with daily salt)
- Browser fingerprints
- User accounts or profiles
- Email addresses
- Device information
- Location data
- Cookies (except essential CSRF)
- Local storage (cleared after post)
- Session data beyond 15 minutes
- View history
- Search history
- Click tracking

### Temporal Data (Auto-Deleted)
```typescript
// Edit tokens expire after 15 minutes
const EDIT_WINDOW = 15 * 60 * 1000; // 15 minutes

// Rate limit data expires after 10 minutes
const RATE_LIMIT_WINDOW = 10 * 60; // 10 minutes

// Daily salt rotation
const SALT_ROTATION = '0 0 * * *'; // Midnight daily
```

## Security Implementation

### Input Sanitization Pipeline
```typescript
function sanitizeUserInput(input: string): string {
  // Step 1: Basic XSS prevention
  let safe = DOMPurify.sanitize(input, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'code', 'pre', 'blockquote', 'a', 'ul', 'ol', 'li'],
    ALLOWED_ATTR: ['href'],
    ALLOW_DATA_ATTR: false
  });
  
  // Step 2: Remove potential PII
  safe = removePII(safe);
  
  // Step 3: Validate length
  if (safe.length > MAX_POST_LENGTH) {
    throw new Error('Post too long');
  }
  
  // Step 4: Check for spam patterns
  if (isLikelySpam(safe)) {
    throw new Error('Post appears to be spam');
  }
  
  return safe;
}

function removePII(text: string): string {
  // Phone numbers
  text = text.replace(/(\+?1?\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})/g, '[phone]');
  
  // Emails
  text = text.replace(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g, '[email]');
  
  // SSN
  text = text.replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[ssn]');
  
  // Credit cards
  text = text.replace(/\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, '[card]');
  
  return text;
}
```

### Image Security
```typescript
async function processUploadedImage(file: File): Promise<ProcessedImage> {
  // Validate file type
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
  if (!allowedTypes.includes(file.type)) {
    throw new Error('Invalid file type');
  }
  
  // Check file size (max 5MB)
  if (file.size > 5 * 1024 * 1024) {
    throw new Error('File too large');
  }
  
  // Process and strip metadata
  const buffer = await file.arrayBuffer();
  const processed = await sharp(buffer)
    .rotate() // Auto-rotate based on EXIF
    .removeMetadata() // Strip ALL metadata
    .resize(1920, 1920, {
      fit: 'inside',
      withoutEnlargement: true
    })
    .jpeg({ 
      quality: 85,
      progressive: true 
    })
    .toBuffer();
  
  // Generate random filename
  const filename = `${generateId()}.jpg`;
  
  return {
    buffer: processed,
    filename,
    size: processed.length
  };
}
```

### Rate Limiting Strategy
```typescript
class RateLimiter {
  private redis: Redis;
  
  async checkPostLimit(ipHash: string): Promise<boolean> {
    const key = `rate:post:${ipHash}`;
    const count = await this.redis.incr(key);
    
    if (count === 1) {
      await this.redis.expire(key, 600); // 10 minutes
    }
    
    // 1 post per 10 minutes
    return count <= 1;
  }
  
  async checkFlagLimit(ipHash: string): Promise<boolean> {
    const key = `rate:flag:${ipHash}`;
    const count = await this.redis.incr(key);
    
    if (count === 1) {
      await this.redis.expire(key, 3600); // 1 hour
    }
    
    // 5 flags per hour
    return count <= 5;
  }
  
  async checkSearchLimit(ipHash: string): Promise<boolean> {
    const key = `rate:search:${ipHash}`;
    const count = await this.redis.incr(key);
    
    if (count === 1) {
      await this.redis.expire(key, 60); // 1 minute
    }
    
    // 30 searches per minute
    return count <= 30;
  }
}
```

### CAPTCHA Implementation
```typescript
// Simple math CAPTCHA to avoid external services
function generateCaptcha(): Captcha {
  const num1 = Math.floor(Math.random() * 10) + 1;
  const num2 = Math.floor(Math.random() * 10) + 1;
  const operations = ['+', '-', '*'];
  const operation = operations[Math.floor(Math.random() * operations.length)];
  
  let answer: number;
  let question: string;
  
  switch (operation) {
    case '+':
      answer = num1 + num2;
      question = `${num1} + ${num2}`;
      break;
    case '-':
      answer = num1 - num2;
      question = `${num1} - ${num2}`;
      break;
    case '*':
      answer = num1 * num2;
      question = `${num1} × ${num2}`;
      break;
  }
  
  // Store in Redis with short TTL
  const id = generateId();
  await redis.setex(`captcha:${id}`, 300, answer.toString());
  
  return { id, question };
}
```

## Anonymity Features

### IP Hashing System
```typescript
class IPHasher {
  private dailySalt: string;
  
  constructor() {
    this.rotateSalt();
    // Rotate daily at midnight
    cron.schedule('0 0 * * *', () => this.rotateSalt());
  }
  
  private rotateSalt(): void {
    this.dailySalt = crypto.randomBytes(32).toString('hex');
    console.log('Daily salt rotated');
  }
  
  hashIP(ip: string): string {
    return crypto
      .createHash('sha256')
      .update(ip + this.dailySalt)
      .digest('hex')
      .substring(0, 16); // Use only first 16 chars
  }
}
```

### Tor Support
```typescript
// Tor-friendly headers
app.use((req, res, next) => {
  // Allow Tor exit nodes
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  
  // Onion-Location header for Tor Browser
  if (process.env.ONION_ADDRESS) {
    res.setHeader('Onion-Location', process.env.ONION_ADDRESS);
  }
  
  next();
});

// Check if request is from Tor
function isFromTor(req: Request): boolean {
  const ip = req.ip;
  // Check against Tor exit node list (updated daily)
  return torExitNodes.includes(ip);
}
```

### Anonymous Name Generation
```typescript
const ADJECTIVES = [
  'Wandering', 'Curious', 'Thoughtful', 'Mysterious', 'Bold',
  'Quiet', 'Restless', 'Dreaming', 'Seeking', 'Questioning',
  'Pondering', 'Exploring', 'Observing', 'Wondering', 'Reflecting'
];

const ANIMALS = [
  'Raven', 'Owl', 'Fox', 'Wolf', 'Bear',
  'Eagle', 'Dolphin', 'Octopus', 'Butterfly', 'Dragonfly',
  'Panther', 'Whale', 'Crow', 'Hawk', 'Salamander'
];

function generateAnonName(): string {
  const adj = ADJECTIVES[crypto.randomInt(ADJECTIVES.length)];
  const animal = ANIMALS[crypto.randomInt(ANIMALS.length)];
  const num = crypto.randomInt(9999);
  
  return `${adj} ${animal} #${num.toString().padStart(4, '0')}`;
}
```

## Security Headers
```typescript
const securityHeaders = {
  'Content-Security-Policy': [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'", // For Next.js
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self'",
    "connect-src 'self'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "upgrade-insecure-requests"
  ].join('; '),
  
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'no-referrer',
  'Permissions-Policy': 'geolocation=(), camera=(), microphone=()',
  
  // Remove fingerprinting vectors
  'Feature-Policy': "accelerometer 'none'; ambient-light-sensor 'none'; autoplay 'none'; battery 'none'; camera 'none'; display-capture 'none'; document-domain 'none'; encrypted-media 'none'; geolocation 'none'; gyroscope 'none'; magnetometer 'none'; microphone 'none'; midi 'none'; payment 'none'; picture-in-picture 'none'; usb 'none'; vibrate 'none'; vr 'none'; wake-lock 'none'; xr-spatial-tracking 'none'"
};
```

## Backup & Data Retention

### Automated Backups
```bash
#!/bin/bash
# Daily backup script

# Backup database
sqlite3 /data/blog.db ".backup '/backups/blog-$(date +%Y%m%d).db'"

# Keep only last 7 days
find /backups -name "blog-*.db" -mtime +7 -delete

# Encrypt backup
gpg --encrypt --recipient backup@example.com /backups/blog-$(date +%Y%m%d).db

# Remove unencrypted
rm /backups/blog-$(date +%Y%m%d).db
```

### Data Retention Policy
- **Posts**: Kept indefinitely (true free speech)
- **IP hashes**: Deleted daily with salt rotation
- **Edit tokens**: Auto-expire after 15 minutes
- **Rate limit data**: Auto-expire per Redis TTL
- **Server logs**: Disabled or piped to /dev/null
- **Error logs**: Sanitized, kept 7 days

## Emergency Response

### If Compromised
1. Take site offline immediately
2. Rotate all salts and secrets
3. Audit recent posts for PII
4. Notify users via site banner
5. Implement additional security measures

### Legal Compliance
- Minimal data = minimal legal exposure
- Clear terms of service
- DMCA compliance process
- Law enforcement guide (explaining minimal data)
- Transparency report (quarterly)

This architecture ensures true anonymity while maintaining a functional platform. The key is collecting nothing that could identify users while still preventing abuse.