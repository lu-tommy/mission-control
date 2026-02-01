# Job Application Tracker

Track applications from discovery through offer with resume versions and follow-ups.

## Schema

```json
{
  "applications": [
    {
      "id": "app-001",
      "company": "Company Name",
      "role": "Job Title",
      "source": "linkedin|indeed|glassdoor",
      "url": "job listing URL",
      "status": "discovery|applied|interviewing|offer|rejected|withdrawn",
      "appliedDate": "2026-02-01",
      "resumeVersion": "v1.2",
      "notes": "fit score, requirements, notes",
      "followups": [],
      "createdAt": "2026-02-01T12:00:00Z"
    }
  ],
  "stats": {
    "total": 0,
    "byStatus": {},
    "bySource": {}
  }
}
```

## Usage

Add new application:
```bash
jq '.applications += [...]' ~/clawd/job-tracker/applications.json > tmp.json && mv tmp.json applications.json
```

Update status:
```bash
jq '.applications[] | select(.id == "app-001") |= .status = "applied"' ...
```

Track follow-up:
```bash
jq '.applications[] | select(.id == "app-001") |= .followups += [{"date": "...", "notes": "..."}]' ...
```

## Best Practices

- Update stats automatically when applications change
- Use unique IDs (app-001, app-002, etc.)
- Include resume version for each application
- Track rejection reasons for learning
