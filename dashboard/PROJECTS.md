# 🦞 Larry's Projects Dashboard

Track all ongoing projects, their status, and progress.

---

## Active Projects

### 🎤 Voice Chat Interface
**Status:** 🟡 In Progress (Frontend complete, API integration pending)
**Priority:** High
**Link:** [http://localhost:8888/voice-chat/](http://localhost:8888/voice-chat/)
**Description:** Voice-enabled chat interface for Larry

**Progress:**
- ✅ Research speech-to-text options
- ✅ Build voice chat UI (HTML/CSS)
- ✅ Implement Web Speech API integration
- ✅ Add TTS for responses
- ✅ Create API server proxy
- ⏳ Integrate with Clawdbot API

**Files:** `/Users/tommylu/clawd/dashboard/voice-chat/`

---

## How It Works

1. **Data Storage**: Projects & tasks stored in `tasks.json`
2. **Rendering**: JavaScript renderer draws to canvas
3. **Updates**: Update `tasks.json`, then re-render
4. **Viewing**: Use canvas tool to display

## Commands

```bash
# Show the dashboard
cd /Users/tommylu/clawd/dashboard
node render-dashboard.js

# Add/update tasks (edit tasks.json directly or use helper scripts)
vim tasks.json

# Refresh dashboard
node render-dashboard.js
```

## Data Structure

```json
{
  "active": [
    {
      "id": "proj-1",
      "title": "Project Name",
      "progress": 45,
      "status": "in-progress",
      "tasks": ["Task 1 done", "Task 2 in progress", "Task 3 pending"],
      "priority": "high"
    }
  ],
  "completed": [
    {
      "id": "proj-2",
      "title": "Finished Project",
      "completedAt": "2025-01-30"
    }
  ]
}
```

## Status Codes

- `in-progress` 🟡 - Active work
- `blocked` 🔴 - Waiting on something
- `review` 🔵 - Needs review/approval
- `completed` ✅ - Done

## Priority Levels

- `high` - Urgent
- `medium` - Normal priority
- `low` - Nice to have
