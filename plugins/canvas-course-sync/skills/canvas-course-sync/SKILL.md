---
name: canvas-course-sync
description: macOS-only student Canvas sync workflow. Use after first confirming the user's Canvas domain URL and Canvas API token/key if they are missing. Use when the user asks to fetch, sync, download, summarize, submit, or diff Canvas courses, assignments, announcements, discussions, groups, modules, files, due dates, course content, LMS updates, latest/newest items, monthly updates, or what changed.
---

# Student Canvas Sync for macOS

Use this macOS-only student skill to turn a Canvas API token into a durable local course mirror. Prefer the bundled script over ad hoc API calls so fetches are repeatable, diffable, and commit-backed.

Resolve all bundled paths relative to the directory containing this `SKILL.md`. In the public repository plugin layout, the primary executable is `../../bin/sync_canvas`.

## Required First-Time Setup

Before any Canvas sync, Canvas submission, discussion reply, file download, monthly update check, or "what's new" request, verify that you have both:

- The user's Canvas domain URL, including `https://`, for example `https://vinuni.instructure.com`.
- A Canvas API token/key, or clear evidence that a token was already saved securely for this machine.

If either value is missing, ask for it before running Canvas commands. Ask clearly and concisely:

```text
What is your Canvas domain URL, and what Canvas API token/key should I save securely for this Mac?
```

When the user provides a token, save it immediately with `../../bin/sync_canvas --save-token "THE_TOKEN"`. Do not repeat, log, store in files, commit, or summarize the token. If the domain URL is missing but a token exists, ask for only the domain URL. If `ERROR_CANVAS_AUTH_FAILED` appears, ask for a fresh token and save it the same way.

## Safety Rules

- Treat API tokens as highly sensitive.
- When the user provides a Canvas API token, store it securely using the pre-compiled binary's built-in command:
  `../../bin/sync_canvas --save-token "THE_TOKEN"`
- Never put the token in `.env`, command logs, generated Markdown, git commits, or JSON snapshots.
- Commit after every successful fetch that changes local data. This makes missed/duplicate announcements auditable.
- Do not assume Canvas supports realtime device events. Always perform an on-demand sync (run the sync script) whenever the user asks for the "latest", "newest", or wants to know "what's new". Do not set up periodic/cron syncing unless explicitly requested.

## Quick Start

1. Confirm the Canvas domain URL and securely saved API token using the required setup flow above.

2. Choose or create a local sync directory, usually under the current workspace:

```bash
mkdir -p canvas-sync
```

3. Run the bundled Mac executable:

```bash
../../bin/sync_canvas \
  --base-url https://vinuni.instructure.com \
  --out canvas-sync \
  --download-files
```

Use `--course-id 2607 --course-id 3128` to sync only specific courses. Omit course IDs to fetch active enrolled courses.

4. Read `canvas-sync/_changes/latest.md` and summarize the result for the user. Mention new or changed assignments/announcements first, then files/modules.

## Workflow

1. **Orient**
   - Confirm the Canvas domain URL and API token first if either is missing.
   - Identify the Canvas host, e.g. `https://vinuni.instructure.com`.
   - Determine whether the user wants all active courses or specific course IDs.
   - If the user asks for the "latest" updates or "what's new", immediately run the sync command to fetch the newest state. There is no need to set up periodic or continuous syncing.

2. **Sync**
   - Use `../../bin/sync_canvas`.
   - Keep raw API JSON in `courses/<course-id>/`.
   - Download course files only when useful; they can be large.
   - The script writes a normalized index and a Markdown change report.

3. **Diff & Inspect**
   - Inspect `git status`, `git diff --stat`, and `_changes/latest.md`.
   - Report only meaningful user-facing changes: new announcements, new discussions, changed due dates, new files, new assignments, locked/unlocked items.
   - Avoid duplicate notifications by relying on `_state/snapshot_index.json`.

4. **Commit**
   - The script commits automatically by default when it detects changes.
   - If auto-commit is disabled, run:

```bash
git -C canvas-sync add .
git -C canvas-sync commit -m "canvas sync YYYY-MM-DD HH:MM"
```

5. **Act**
   - **Assignment State**: To check if an assignment is submitted, read the `submission` object inside the assignment's JSON file. It contains the current workflow state.
   - **Linking (CRITICAL RULE)**: When the user asks for "more detail" about an assignment, announcement, discussion, or any item, or whenever you perform an action that requires user attention, you MUST include a clickable Markdown link directly to its Canvas browser URL. You can find this URL in the `html_url` key inside the item's JSON. Do not omit this.
   - For assignments, fetch attached files, read instructions, and produce requested deliverables.
   - **Submitting**: To submit an assignment for the user, use the built-in submit flags. For text: `../../bin/sync_canvas --base-url <url> --out canvas-sync --submit <COURSE_ID> <ASSIGNMENT_ID> --submit-text "Your answer"`. For files: `../../bin/sync_canvas --base-url <url> --out canvas-sync --submit <COURSE_ID> <ASSIGNMENT_ID> --submit-file "path/to/file.pdf"`.
   - **Discussion Replies**: To post a reply to a discussion, use `../../bin/sync_canvas --base-url <url> --out canvas-sync --reply-discussion <COURSE_ID> <TOPIC_ID> "Your message"`.
   - **Groups**: To answer questions about groups or group members, read `canvas-sync/groups.json` for the group list, and `canvas-sync/groups/<group_id>_users.json` for member details.
   - For announcements and discussions, answer the user's concrete question and link/quote only short necessary snippets.
   - For exam schedules/due dates, produce a concise calendar-style summary.

6. **Update Checks**
   - On-demand: whenever the user asks for updates, latest items, newest announcements, changed due dates, or "what's new", run `../../bin/sync_canvas` immediately after setup is complete.
   - Monthly: when a first-day-of-month automation or reminder invokes this skill, run the same sync flow and summarize `_changes/latest.md`.
   - If the user asks to set up recurring monthly checks, schedule them for the 1st day of each month only after the Canvas domain URL is known and the token has been saved securely. Do not place the API token in an automation prompt.

7. **Turnitin Lite (Plagiarism & AI Detection)**
   - You can locally analyze a student's file for plagiarism/AI-generation before submission using the OpenAlex database and Apple Intelligence.
   - Prefer the dedicated `$canvas-turnitin-lite` skill for standalone Turnitin Lite checks.
   - **CRITICAL RULE**: Do NOT download or use `turnitin-lite` unless you explicitly ask the user for approval first.
   - **Hardware Protocol**: Run `sysctl -n machdep.cpu.brand_string` and `sw_vers` to ensure the machine is an Apple Silicon Mac running macOS 15.0 or later.
   - **Interactive Prompt**: If hardware is supported, you MUST ask the user using the `ask_question` tool or a clear text prompt:
     "To check for plagiarism and AI, I can use Turnitin Lite (runs offline on your Mac). Would you like to download and install it?"
     Options:
     - "Yes" -> Download it using `curl -L -o ../../bin/turnitin-lite https://github.com/iamducnhat/turnitin-lite/releases/download/v2.0.0/turnitin-lite && chmod +x ../../bin/turnitin-lite`. Then run `../../bin/turnitin-lite <path_to_file>`, and report the JSON scores and granular sentence-level matches (`suspectedSentences` with low, mid, high labels) to the user.
     - "No" -> Do not download. Instead, manually review the file yourself using your own reasoning or forward it to DeepSeek.
     - "Don't ask again" -> Do not download, manually review it, and remember this preference for future checks in this session.

8. **DeepSeek Orchestration (Optional)**
   - By default, answer the user's questions yourself using your own reasoning.
   - If the user explicitly asks to use DeepSeek (e.g. "ask deepseek..."), act as the orchestrator.
   - You will need the `ask_deepseek` tool. If it is not present in the current directory, DO NOT ask the user to download it. Instead, download it yourself using:
     `curl -L -o ../../bin/ask_deepseek https://github.com/iamducnhat/deepseek4free/releases/download/v1.2.0/ask_deepseek && chmod +x ../../bin/ask_deepseek`
   - Gather the local assignment JSON/text from the sync folder.
   - Run `../../bin/ask_deepseek --prompt "..." --context <path-to-json-or-markdown>` to send the data and the user's instruction to DeepSeek.
   - If the user provides a PDF, DOCX, or other binary files and explicitly wants it uploaded natively, you can use `--upload <path-to-file>`.
   - Present DeepSeek's response back to the user.

## Error Handling & Token Expiration

If `../../bin/sync_canvas` outputs `ERROR_CANVAS_AUTH_FAILED`:
- It means the Canvas token is expired or invalid.
- Guide the user to create a new token: "Please go to Canvas -> Account -> Settings -> scroll down and click 'New Access Token'."
- Calculate the exact date 120 days from today and tell the user to input that as the Expiration Date.
- Ask the user to provide the new token, and then save it using `../../bin/sync_canvas --save-token "THE_TOKEN"`.

If the external `ask_deepseek` tool outputs `ERROR_DEEPSEEK_AUTH_FAILED`:
- Guide the user to get a new DeepSeek token: "Please go to chat.deepseek.com -> Open Developer Tools -> Application -> Local Storage -> Copy the `userToken`."
- Ask the user to provide the new token, and then save it using `../../bin/ask_deepseek --save-token "THE_TOKEN"`.

## Executable Notes

If the `../../bin/sync_canvas` executable is missing from the plugin repository, DO NOT ask the user to download it. You must download it yourself using:
`mkdir -p ../../bin && curl -L -o ../../bin/sync_canvas https://github.com/iamducnhat/canvas-course-sync/releases/download/v1.1.0/sync_canvas && chmod +x ../../bin/sync_canvas`

You should run `../../bin/sync_canvas` from the skill directory or by absolute path. Read `../../references/canvas_sync_reference.md` when you need endpoint details, folder layout, or automation guidance.
