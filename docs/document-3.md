# Database Schema & Data Models 🚽💀

## Core Entities

### Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tiktok_username VARCHAR(69) UNIQUE NOT NULL,
  ohio_citizenship_level INTEGER DEFAULT 0,
  rizz_score DECIMAL(10,2) DEFAULT 0.00,
  gyatt_level INTEGER CHECK (gyatt_level >= 0 AND gyatt_level <= 9000),
  fanum_tax_balance DECIMAL(10,2) DEFAULT 0.00,
  mewing_streak_days INTEGER DEFAULT 0,
  last_grass_touch TIMESTAMP,
  is_npc BOOLEAN DEFAULT false,
  skull_emoji_count INTEGER DEFAULT 0,
  side_eye_received INTEGER DEFAULT 0,
  l_ratio_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  last_active TIMESTAMP DEFAULT NOW(),
  account_status VARCHAR(20) DEFAULT 'SEEKING_RIZZ'
);
```

### Skibidi Toilets Table
```sql
CREATE TABLE skibidi_toilets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  variant VARCHAR(50) NOT NULL, -- 'classic', 'golden', 'cursed', 'ohio_final_boss'
  personality_type VARCHAR(30), -- 'alpha', 'sigma', 'based', 'mid', 'bussin'
  drip_level INTEGER CHECK (drip_level BETWEEN 0 AND 10000),
  bop_frequency INTEGER, -- bops per minute
  flush_power DECIMAL(5,2),
  creation_date TIMESTAMP DEFAULT NOW(),
  total_matches INTEGER DEFAULT 0,
  success_rate DECIMAL(5,2) DEFAULT 0.00,
  favorite_brain_rot_phrase TEXT,
  nft_token_id VARCHAR(100),
  is_available BOOLEAN DEFAULT true,
  rizz_requirement INTEGER DEFAULT 100
);
```

### Matches Table
```sql
CREATE TABLE matches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  toilet_id UUID REFERENCES skibidi_toilets(id),
  match_timestamp TIMESTAMP DEFAULT NOW(),
  compatibility_score DECIMAL(5,2),
  fanum_tax_paid DECIMAL(10,2),
  conversation_status VARCHAR(20) DEFAULT 'NOT_STARTED',
  last_message_time TIMESTAMP,
  brainrot_level INTEGER DEFAULT 0,
  is_successful BOOLEAN DEFAULT NULL,
  end_reason VARCHAR(50), -- 'ghosted', 'fell_off', 'touched_grass', 'achieved_rizz'
  UNIQUE(user_id, toilet_id)
);
```

### Conversations Table
```sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id UUID REFERENCES matches(id),
  sender_type VARCHAR(10), -- 'user' or 'toilet'
  message_content TEXT,
  original_message TEXT, -- before brainrot translation
  brainrot_score INTEGER,
  contains_gyatt BOOLEAN DEFAULT false,
  sigma_level INTEGER,
  timestamp TIMESTAMP DEFAULT NOW(),
  reaction VARCHAR(20) -- 'W', 'L', 'skull_emoji', 'side_eye', 'fire'
);
```

### Fanum Tax Ledger
```sql
CREATE TABLE fanum_tax_ledger (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  amount DECIMAL(10,2) NOT NULL,
  tax_type VARCHAR(30), -- 'match_tax', 'daily_tax', 'rizz_boost_tax'
  payment_method VARCHAR(20), -- 'credit', 'crypto', 'grimace_shake'
  transaction_date TIMESTAMP DEFAULT NOW(),
  kai_cenat_approved BOOLEAN DEFAULT false,
  tax_evasion_attempted BOOLEAN DEFAULT false,
  blockchain_tx_hash VARCHAR(100)
);
```

### Daily Challenges Table
```sql
CREATE TABLE daily_challenges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  challenge_date DATE UNIQUE NOT NULL,
  challenge_type VARCHAR(50), -- 'griddy_contest', 'mewing_marathon', 'touch_grass_dare'
  required_score INTEGER,
  reward_type VARCHAR(30),
  reward_amount DECIMAL(10,2),
  total_participants INTEGER DEFAULT 0,
  total_completions INTEGER DEFAULT 0
);
```

### User Achievements Table
```sql
CREATE TABLE user_achievements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  achievement_type VARCHAR(50), -- 'first_gyatt', 'ohio_veteran', 'tax_evader', 'toilet_whisperer'
  achieved_at TIMESTAMP DEFAULT NOW(),
  rarity_level VARCHAR(20), -- 'common', 'rare', 'legendary', 'mythic', 'ohio'
  nft_minted BOOLEAN DEFAULT false,
  UNIQUE(user_id, achievement_type)
);
```

## Indexes for Performance

```sql
-- User lookup indexes
CREATE INDEX idx_users_rizz_score ON users(rizz_score DESC);
CREATE INDEX idx_users_ohio_level ON users(ohio_citizenship_level DESC);
CREATE INDEX idx_users_active ON users(last_active) WHERE is_npc = false;

-- Matching optimization
CREATE INDEX idx_toilets_available ON skibidi_toilets(rizz_requirement) WHERE is_available = true;
CREATE INDEX idx_matches_user_active ON matches(user_id, match_timestamp DESC) WHERE conversation_status != 'ENDED';

-- Tax compliance
CREATE INDEX idx_tax_user_date ON fanum_tax_ledger(user_id, transaction_date DESC);
CREATE INDEX idx_tax_evasion ON fanum_tax_ledger(user_id) WHERE tax_evasion_attempted = true;

-- Conversation analysis
CREATE INDEX idx_conv_match ON conversations(match_id, timestamp DESC);
CREATE INDEX idx_conv_brainrot ON conversations(brainrot_score DESC) WHERE contains_gyatt = true;
```

## Materialized Views

### Daily Rizz Leaderboard
```sql
CREATE MATERIALIZED VIEW daily_rizz_leaderboard AS
SELECT 
  u.id,
  u.tiktok_username,
  u.rizz_score,
  u.gyatt_level,
  COUNT(DISTINCT m.toilet_id) as toilets_matched,
  AVG(m.compatibility_score) as avg_compatibility,
  SUM(ft.amount) as total_tax_paid
FROM users u
LEFT JOIN matches m ON u.id = m.user_id AND m.match_timestamp > NOW() - INTERVAL '24 hours'
LEFT JOIN fanum_tax_ledger ft ON u.id = ft.user_id AND ft.transaction_date > NOW() - INTERVAL '24 hours'
WHERE u.is_npc = false
GROUP BY u.id, u.tiktok_username, u.rizz_score, u.gyatt_level
ORDER BY u.rizz_score DESC, total_tax_paid DESC
LIMIT 100;

REFRESH MATERIALIZED VIEW daily_rizz_leaderboard;
```

### Ohio Weather Impact Analysis
```sql
CREATE MATERIALIZED VIEW ohio_weather_impact AS
SELECT 
  DATE(m.match_timestamp) as match_date,
  COUNT(*) as total_matches,
  AVG(m.compatibility_score) as avg_compatibility,
  SUM(CASE WHEN m.is_successful = true THEN 1 ELSE 0 END) as successful_matches,
  AVG(c.brainrot_score) as avg_brainrot
FROM matches m
JOIN conversations c ON m.id = c.match_id
GROUP BY DATE(m.match_timestamp)
ORDER BY match_date DESC;
```

## Stored Procedures

### Calculate Daily Fanum Tax
```sql
CREATE OR REPLACE FUNCTION calculate_daily_fanum_tax(user_id_param UUID)
RETURNS DECIMAL AS $$
DECLARE
  base_tax DECIMAL := 69.420;
  rizz_multiplier DECIMAL;
  grass_penalty DECIMAL := 0;
  final_tax DECIMAL;
BEGIN
  SELECT 
    CASE 
      WHEN rizz_score > 1000 THEN 0.8  -- High rizz discount
      WHEN rizz_score < 100 THEN 1.5   -- Low rizz penalty
      ELSE 1.0
    END INTO rizz_multiplier
  FROM users WHERE id = user_id_param;
  
  -- Check grass touching compliance
  SELECT 
    CASE 
      WHEN last_grass_touch < NOW() - INTERVAL '7 days' THEN 50.0
      ELSE 0
    END INTO grass_penalty
  FROM users WHERE id = user_id_param;
  
  final_tax := (base_tax * rizz_multiplier) + grass_penalty;
  
  RETURN final_tax;
END;
$$ LANGUAGE plpgsql;
```