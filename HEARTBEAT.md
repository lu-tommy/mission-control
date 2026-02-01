# HEARTBEAT.md

# Proactive Work & Monitoring

## 🎯 DASHBOARD-FIRST WORKFLOW
**The dashboard is my task queue. Always check it first.**

**Location:** `~/clawd/dashboard/larry-status.json` | URL: http://localhost:8888/

**Every heartbeat or idle moment:**
1. Read `larry-status.json` for current tasks
2. Pick highest priority task from backlog (high > medium > low)
3. Move task to `inProgress`, set `larryStatus: "working"`
4. Work on it, update progress in real-time
5. When done: move to `done`, log completion, set `larryStatus: "idle"`
6. If no tasks: reply HEARTBEAT_OK

**For large projects:**
- Break into subtasks with clear steps
- Use sessions_spawn for GLM execution
- Estimate time, track actual spent

## 🌙 OVERNIGHT MODE (12am - 7am EST)
**Tommy wants SURPRISES when he wakes up. Build things, don't just check things.**

During overnight heartbeats, tackle dashboard tasks:
- [ ] High-priority backlog items first
- [ ] Job search tasks (find roles, prep materials)
- [ ] Portfolio projects (build, document, push to GitHub)
- [ ] System improvements (tools, automations)
- [ ] Skill enhancements (learn, document)

**Goal:** When Tommy wakes up, there should be something tangible he didn't have before.

Update dashboard with progress. Leave morning summary in activity log.

---

## 🧹 Memory Hygiene (Run Daily)
Run `~/clawd/tools/memory-hygiene.sh` to check for:
- Fragment files (YYYY-MM-DD-*.md) that need consolidation
- Oversized daily files (>5KB) that need trimming
- MEMORY.md bloat (>3KB)

If issues found, fix them immediately. Don't let cruft accumulate.

---

# Daytime Monitoring Checklist

# Rotate through these checks 2-4 times per day during market hours (9:30 AM - 4:00 PM ET)
# Outside market hours: minimal checks (weather, bot status)

## Priority Checks (Market Hours)


### 1. Calendar & Schedule
- Upcoming events in next 24-48 hours
- Market closed days/early closes coming up?

## Secondary Checks (Once Daily)

### 2. Weather
- Morning weather check if user might go out
- Evening check if planning next day

### 3. Home Assistant
- Any critical alerts (security, water leaks, etc.)
- Backup status

## When to Proactively Reach Out

**ALWAYS reach out for:**
- Trading bot stopped unexpectedly
- Portfolio dropped >3% in a day
- Circuit breakers triggered
- Database errors
- Security alerts from Home Assistant
- Kalshi bot showing unusual activity (if running)

**Sometimes reach out for:**
- Portfolio trending down significantly (1-2%)
- Multiple rejected trades in a row
- Bot behaving unusually
- Interesting market insights found

**Stay quiet for:**
- Normal bot operation (healthy, making small moves)
- Late night (23:00-08:00) unless urgent
- User just checked <30 min ago
- Nothing new since last check

## Check Frequency

| Check Type | Frequency | When |
|------------|-----------|------|
| Calendar | Morning | Daily |
| Weather | Morning (if relevant) | Daily |
| Home Assistant | Morning | Daily |

## Proactive Work (Do Without Asking)

**Background maintenance:**
- Review and organize memory files (daily → MEMORY.md)
- Update documentation if patterns emerge
- Clean up old session logs
- Git status on project directories
- Check for updates on critical tools

**Example:**
```
cd ~/Desktop/stocktrade/mag7-signal-v10
git status
```

## State Tracking

Track last checks in `memory/heartbeat-state.json`:
```json
{
  "lastChecks": {
    "mag7_bot": 1706659200,
    "docker_status": 1706659200,
    "calendar": 1706659200,
    "weather": null
  }
}
```

## Notes

- User values directness - keep alerts concise
- Include evidence (logs, numbers) when reporting issues
- For critical issues, include what you're doing to fix it
- Normal operation doesn't need reports
