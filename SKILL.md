---
name: canvas-course-sync
description: Sync Instructure Canvas courses using a user's Canvas API token. Use when the user asks Codex to fetch, sync, download, summarize, or diff Canvas courses, assignments, announcements, modules, files, due dates, course content, or LMS updates; when the user asks for the latest/newest items; when the user provides a Canvas API token; or when Codex needs a durable folder/git workflow for Canvas data without missing or duplicating new notices.
---

# Canvas Course Sync

Use this skill to turn a Canvas API token into a durable local course mirror. Prefer the bundled script over ad hoc API calls so fetches are repeatable, diffable, and commit-backed.

## Safety Rules

- Treat Canvas API tokens as secrets. Do not print, quote, commit, or include them in final answers.
- If the user pastes a token, use it only for the current sync or store it outside the sync repo with `chmod 600` when persistence is useful.
- Never put the token in `.env`, command logs, generated Markdown, git commits, or JSON snapshots.
- Commit after every successful fetch that changes local data. This makes missed/duplicate announcements auditable.
- Do not assume Canvas supports realtime device events. Always perform an on-demand sync (run the sync script) whenever the user asks for the "latest", "newest", or wants to know "what's new". Do not set up periodic/cron syncing unless explicitly requested.

## Quick Start

1. Choose or create a local sync directory, usually under the current workspace:

```bash
mkdir -p canvas-sync
```

2. Run the bundled Mac executable:

```bash
~/.codex/skills/canvas-course-sync/bin/sync_canvas \
  --base-url https://vinuni.instructure.com \
  --token "$CANVAS_API_TOKEN" \
  --out canvas-sync \
  --download-files
```

Use `--course-id 2607 --course-id 3128` to sync only specific courses. Omit course IDs to fetch active enrolled courses.

3. Read `canvas-sync/_changes/latest.md` and summarize the result for the user. Mention new or changed assignments/announcements first, then files/modules.

## Workflow

1. **Orient**
   - Identify the Canvas host, e.g. `https://vinuni.instructure.com`.
   - Determine whether the user wants all active courses or specific course IDs.
   - If the user asks for the "latest" updates or "what's new", immediately run the sync command to fetch the newest state. There is no need to set up periodic or continuous syncing.

2. **Sync**
   - Use `bin/sync_canvas`.
   - Keep raw API JSON in `courses/<course-id>/`.
   - Download course files only when useful; they can be large.
   - The script writes a normalized index and a Markdown change report.

3. **Diff**
   - Inspect `git status`, `git diff --stat`, and `_changes/latest.md`.
   - Report only meaningful user-facing changes: new announcements, changed due dates, new files, new assignments, locked/unlocked items.
   - Avoid duplicate notifications by relying on `_state/snapshot_index.json`.

4. **Commit**
   - The script commits automatically by default when it detects changes.
   - If auto-commit is disabled, run:

```bash
git -C canvas-sync add .
git -C canvas-sync commit -m "canvas sync YYYY-MM-DD HH:MM"
```

5. **Act**
   - For assignments, fetch attached files, read instructions, and produce requested deliverables.
   - For announcements, answer the user's concrete question and link/quote only short necessary snippets.
   - For exam schedules/due dates, produce a concise calendar-style summary.

6. **DeepSeek Orchestration (Optional)**
   - By default, answer the user's questions yourself using your own reasoning.
   - If the user explicitly asks to use DeepSeek (e.g. "bảo deepseek..."), act as the orchestrator.
   - Gather the local assignment JSON/text from the sync folder.
   - Run `bin/ask_deepseek --prompt "..." --context <path-to-json-or-markdown>` to send the data and the user's instruction to DeepSeek.
   - Present DeepSeek's response back to the user.

## Executable Notes

The main executable is:

```bash
~/.codex/skills/canvas-course-sync/bin/sync_canvas
```

Read `references/canvas_sync_reference.md` when you need endpoint details, folder layout, or automation guidance.
