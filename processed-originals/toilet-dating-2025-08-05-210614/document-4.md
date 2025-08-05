# UI/UX Design Specifications 🎨💀

## Design Philosophy
"If it doesn't cause immediate psychic damage, it's not brainrot enough" - Ancient Ohio Proverb

## Color Palette

### Primary Colors
- **Skibidi Blue**: #1E90FF (represents toilet water)
- **Ohio Gray**: #808080 (eternal overcast vibes)
- **Rizz Red**: #FF1744 (for W moments)
- **Fanum Green**: #00E676 (money/tax color)
- **Brainrot Purple**: #7C4DFF (mental degradation)

### Accent Colors
- **Gyatt Gold**: #FFD700 (premium features)
- **NPC Beige**: #F5DEB3 (default user state)
- **Sigma Black**: #000000 (grindset mode)
- **Touch Grass Green**: #228B22 (warning color)

## Typography

### Font Stack
```css
font-family: 'Comic Sans MS', 'Papyrus', 'Impact', cursive;
/* If user complains, add more Comic Sans */
```

### Font Sizes
- Hero Text: 69px (nice)
- Headers: 42px (the answer)
- Body Text: 16px (readability is for NPCs)
- Fine Print: 8px (fanum tax terms)

## Component Library

### 1. Rizz-O-Meter Component
```jsx
<RizzOMeter 
  currentRizz={user.rizzScore}
  maxRizz={6900}
  animate="pulse"
  glowColor="rizz-red"
  label="YOUR RIZZ LEVEL FR FR"
/>
```

Visual: Animated bar that violently shakes when rizz increases

### 2. Skibidi Toilet Card
```jsx
<SkibidiToiletCard
  variant={toilet.variant}
  dripLevel={toilet.dripLevel}
  animation="bop-bop"
  sound="yes-yes.mp3"
  onClick={() => matchWithToilet(toilet.id)}
/>
```

Features:
- 3D rotating toilet model
- Particle effects for high drip levels
- Plays toilet sounds on hover
- Rainbow border for legendary variants

### 3. Fanum Tax Calculator
```jsx
<FanumTaxCalculator
  baseAmount={69.42}
  taxRate={0.20}
  showKaiCenatApproval={true}
  evasionButton={true}
  onEvade={() => alert("IRS NOTIFIED 🚨")}
/>
```

### 4. Mewing Timer Widget
```jsx
<MewingTimer
  streakDays={user.mewingStreak}
  currentSession={mewingTime}
  leaderboardPosition={user.rank}
  motivationalQuote="KEEP MEWING KING 👑"
/>
```

## Page Layouts

### Landing Page
- Full-screen video of Skibidi Toilets dancing
- "ENTER OHIO" button (minimum 200px height)
- Seizure warning in 6px font
- Auto-playing Gen Alpha anthem
- Floating "GYATT" text elements

### Profile Creation
1. TikTok Authentication (mandatory)
2. Rizz Assessment Quiz
   - "How often do you say 'no cap'?"
   - "Rate your Ohio knowledge 1-10"
   - "Last time you touched grass?"
3. Profile Picture: Must include toilet in background
4. Bio: 280 character limit, must contain at least 3 Gen Alpha terms

### Main Dating Interface
- Tinder-style swipe mechanism
- Toilet appears with stats overlay
- Background: Constantly shifting Ohio weather
- Bottom bar: Rizz level, Fanum tax due, Mewing timer
- Random "WHAT THE SIGMA" popups

### Chat Interface
- Messages appear in speech bubbles
- Toilet messages in "Skibidi" font
- Auto-translation toggle for brainrot speak
- Emoji reactions limited to: 💀, 🔥, 📸, 🤨, 🚽
- "GYATT" button for emphasis

## Animations & Interactions

### Micro-interactions
- Every button click: Screen shake effect
- Successful match: Toilet flush sound + confetti
- Failed match: "L + RATIO" falls from top
- Tax payment: Cash register "cha-ching"
- Level up: Airhorn sound effect

### Loading States
- Spinning toilet animation
- Loading text: "GRINDING...", "HITTING THE GRIDDY...", "ACQUIRING RIZZ..."
- Progress bar fills with toilet water texture

### Error States
- 404 Page: "YOU'RE LOST IN OHIO BRO"
- Network Error: "NO SIGNAL (JUST LIKE OHIO)"
- Payment Failed: "FANUM TAX EVASION DETECTED"
- Server Error: "SKIBIDI TOILET OVERFLOW"

## Mobile Considerations

### Responsive Design
- Mobile-first (Gen Alpha doesn't use computers)
- Thumb-friendly swipe zones
- Vertical video format for all content
- Mandatory portrait mode
- Shake-to-refresh (literally shake phone)

### Touch Gestures
- Swipe right: W (match)
- Swipe left: L (pass)
- Swipe up: Super Gyatt (premium like)
- Swipe down: Report for being an NPC
- Long press: View toilet stats
- Pinch: Zoom on toilet details

## Accessibility Features
- Screen reader: Reads everything in Gen Alpha slang
- High contrast mode: Even more eye-bleeding colors
- Reduced motion: Removes 90% of app functionality
- Captions: All toilet sounds transcribed as "skibidi bop"

## Dark Mode
There is no dark mode. Ohio is permanently overcast.

## Easter Eggs
- Konami code: Unlocks secret "Grimace Toilet" variant
- Triple tap logo: Plays full Skibidi Toilet episode
- Shake phone 10 times: "GO TOUCH GRASS" notification
- Type "OHIO": Map shows your exact location as Ohio

## Performance Metrics
- First Contentful Paint: < 420ms
- Time to Interactive: < 690ms
- Rage quit rate: < 80%
- Seizure induction rate: < 5%
- User retention: Measured in "attention spans" (3-5 seconds)