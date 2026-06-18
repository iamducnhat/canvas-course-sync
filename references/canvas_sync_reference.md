# Canvas Sync Reference

## Endpoint Coverage

The bundled sync script fetches:

- active enrolled courses: `GET /api/v1/courses`
- course details: `GET /api/v1/courses/:course_id` (includes syllabus_body)
- assignments: `GET /api/v1/courses/:course_id/assignments`
- assignment detail: `GET /api/v1/courses/:course_id/assignments/:assignment_id`
- pages: `GET /api/v1/courses/:course_id/pages`
- page detail: `GET /api/v1/courses/:course_id/pages/:url`
- quizzes: `GET /api/v1/courses/:course_id/quizzes`
- modules: `GET /api/v1/courses/:course_id/modules`
- module items: `GET /api/v1/courses/:course_id/modules/:module_id/items`
- announcements: `GET /api/v1/courses/:course_id/discussion_topics?only_announcements=true`
- discussions: `GET /api/v1/courses/:course_id/discussion_topics`
- files: `GET /api/v1/courses/:course_id/files`

Canvas pagination uses the HTTP `Link` header. Always follow `rel="next"` until exhausted.

## Folder Layout

```text
canvas-sync/
  _changes/
    latest.md
    sync-YYYYMMDD-HHMMSS.md
  _state/
    snapshot_index.json
  courses/
    <course-id>/
      course.json
      assignments.json
      assignments/
        <assignment-id>.json
      announcements.json
      discussions.json
      pages.json
      pages/
        <page-url>.json
      quizzes.json
      files.json
      files/
        <file-id>-<filename>
      modules.json
      modules/
        <module-id>-items.json
  index.json
```

## De-duplication Model

Each fetched object gets a stable key:

```text
<course-id>:<type>:<object-id>
```

The state index stores a content hash, `updated_at` when available, and a short summary. A later sync is:

- `new` when the key does not exist.
- `changed` when the hash differs.
- ignored when the key and hash are unchanged.

Use this state instead of visually scanning downloaded files for notification logic.

## Git Discipline

Initialize git in the sync directory if absent. Commit after each successful sync with a message like:

```text
canvas sync 2026-06-18 22:30
```

This gives a permanent audit trail. Use `git log --oneline`, `git show --stat`, and `git diff HEAD~1..HEAD` to explain what changed.

## Token Handling

Preferred order:

1. `CANVAS_API_TOKEN` environment variable for one-off runs.
2. `--token-file ~/.canvas_tokens/<host>.token` with file mode `600`.
3. `--token <token>` only when unavoidable; do not save shell history snippets containing it in user-visible docs.

Never commit token files.

## On-Demand Syncing

Whenever the user asks for the "latest" items, "newest" announcements, or wants to know "what changed", you must run the sync script immediately to fetch the newest data. Do not set up periodic syncing (like cron or Codex heartbeat) because pulling on-demand is sufficient and preferred. After the script finishes, inspect `_changes/latest.md` and report the new/changed items to the user.
