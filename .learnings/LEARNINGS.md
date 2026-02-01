# Learnings - Self-Improvement Log

This file tracks learnings, corrections, and discoveries for continuous improvement.

---

## [LRN-20260201-001] voice-chat-prompt-structure

**Logged**: 2026-02-01T19:35:00Z
**Priority**: high
**Status**: resolved
**Area**: config

### Summary
Voice chat was using overly-complex prompt wrapper that caused GLM 4.7 to give generic non-responses

### Details
Original server.js prompt:
```
`Voice chat message from Tommy. Be conversational, warm, brief (2-3 sentences max).
Answer questions directly. Do NOT use tools unless specifically asked.
Reply with TEXT ONLY. He said: "${message}"`
```

This caused GLM to ignore the actual message and give generic responses like "What can I help with?"

### Fix
Pass message directly to `sessions_spawn` without wrapper:
```javascript
const spawnResult = await callClawdbot('sessions_spawn', {
  task: message,  // Direct, no wrapper
  model: 'zai/glm-4.7',
  timeoutSeconds: 30,
  cleanup: 'delete',
  label: 'voice-chat',
  thinking: 'low'
});
```

Also set `thinking: 'low'` instead of 'off' for better balance.

### Resolution
- **Resolved**: 2026-02-01T19:26:00Z
- **Files**: /Users/tommylu/clawd/dashboard/voice-chat/server.js
- **Notes**: Voice chat now responds correctly to questions

### Metadata
- Source: user_feedback
- Related Files: ~/clawd/dashboard/voice-chat/server.js
- Tags: voice, prompt-optimization, glm
- See Also:

---

## [LRN-20260201-002] self-optimization-workflow

**Logged**: 2026-02-01T19:35:00Z
**Priority**: high
**Status**: in_progress
**Area**: infra

### Summary
Set up .learnings/ directory structure for continuous improvement tracking

### Details
Created .learnings/ directory with:
- LEARNINGS.md - For lessons learned, corrections, knowledge gaps
- ERRORS.md - For tracking failures and issues

This follows the self-improvement skill pattern to capture:
- User corrections ("No, that's wrong...")
- Unexpected command failures
- Missing feature requests
- Knowledge gaps
- Better approaches discovered

### Action Items
- Add periodic learning review cron job (weekly?)
- Promote learnings to AGENTS.md, TOOLS.md, SOUL.md as applicable
- Review learnings before major tasks
- Add to AGENTS.md: self-improvement workflow

### Metadata
- Source: proactive_setup
- Related Files: ~/.learnings/LEARNINGS.md, ~/.learnings/ERRORS.md
- Tags: self-improvement, learning-system, workflow
- See Also:

---

## [LRN-20260201-003] cron-job-learning-review

**Logged**: 2026-02-01T19:36:00Z
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
Added weekly cron job for learning review (Saturdays at 6pm ET)

### Details
Cron job: `learning-review`
- Schedule: `0 18 * * 6` (Saturdays 6pm)
- Action: Reviews `.learnings/LEARNINGS.md` and `.learnings/ERRORS.md`
- Promotes high-value learnings to AGENTS.md, TOOLS.md, SOUL.md
- Marks resolved items with status updates

### Metadata
- Source: proactive_setup
- Related Files: N/A (cron job)
- Tags: cron, automation, learning-system
- See Also:

---

