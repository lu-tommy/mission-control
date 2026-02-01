# Twitter API Research - Larry the Lobster 🦞

## Research Date: 2026-01-30

## X API v2 Pricing (Official API)

### Free Tier ✅ (WHAT WE'LL USE)
- **Cost:** Free
- **Posts:** 500 posts/month (~16 posts/day - plenty for Larry!)
- **Reads:** 100 reads/month (very limited)
- **Use case:** Write-only (posting only, minimal reading)
- **Projects:** 1 project, 1 app
- **Limitations:** Write-only use cases, testing

### Basic Tier
- **Cost:** $175-200/month
- **Posts:** 3,000 posts/month (user level)
- **Reads:** 10,000 reads/month
- **Not needed:** Overkill for our needs

### Pro Tier
- **Cost:** $4,500-5,000/month
- Way beyond what we need

## Tweepy (Python Library)

- Official Twitter Python library
- Supports X API v2
- Installation: `pip install tweepy`
- Uses official API keys (API key, API secret, Access token, Access token secret)
- **Works with Free tier** ✅

## Bird CLI Status

- **Status:** BLOCKED by Twitter anti-spam (Error 226: "looks like automated")
- **Reason:** Twitter detected automated posting pattern
- **Workaround:** Wait for flag to reset OR use official API

## Recommended Solution: Tweepy + X API Free Tier

### Why This Works:
1. ✅ **Free** - No cost (500 posts/month limit)
2. ✅ **Legitimate** - Uses official API, not blocked as spam
3. ✅ **Sufficient** - 500/month = 16/day (Larry needs 4-6/day)
4. ✅ **Python** - Easy to integrate with Cron jobs
5. ✅ **Stable** - Official support, won't break unexpectedly

### Limitations:
- Read limit: 100/month (can't do much engagement/reading)
- Write-only (posting focus)
- Need to get API keys from X Developer Portal

### Implementation Plan:
1. Create X Developer account (free)
2. Create project/app
3. Get API credentials
4. Build Python script with Tweepy
5. Set up cron jobs for scheduled posting
6. Generate content with Larry's persona

## Alternative: Continue with Bird CLI

- Wait for Twitter's automated flag to reset (few hours to 24h)
- Try posting with longer delays between tweets
- Risk: May get blocked again quickly

## Decision: Use Tweepy

**Tweepy + X API Free Tier is the way to go.** It's free, legitimate, and will work reliably for Larry's posting needs.

## Next Steps:
1. User creates X Developer account (free)
2. User gets API keys
3. I build Tweepy bot
4. Set up automation

## Notes:
- Bird CLI uses cookie-based auth (bypasses API but gets flagged as spam)
- Official API uses proper authentication (doesn't get flagged as spam)
- Free tier is specifically designed for "write-only use cases and testing" - perfect fit
