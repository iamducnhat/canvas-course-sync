# Canvas Course Sync

A lightweight, local-first tool and Codex skill for syncing Instructure Canvas courses into a durable, git-backed directory.

This tool uses your Canvas API token to fetch course data (assignments, announcements, pages, quizzes, modules, and files) and normalizes it into JSON files. It generates a Markdown report of changes after each sync and optionally commits the state to a local git repository. This provides a clean, auditable history of your course updates without missing or duplicating notices.

## Features

- **Comprehensive Data Sync:** Fetches active courses, assignments (and full details), announcements, modules, pages, quizzes, and files.
- **Git-Backed Auditing:** Automatically initializes a git repository and commits changes upon each successful sync, ensuring a permanent audit trail.
- **Change Detection:** Uses content hashing to determine exactly what is new or modified.
- **Reporting:** Generates a human-readable Markdown report (`_changes/latest.md`) summarizing what changed.
- **On-Demand Syncing:** Built to be run exactly when you need to know "what's new", fetching the latest state directly from Canvas.

## Prerequisites

- Python 3.9 or newer.
- A Canvas LMS instance (e.g., `https://canvas.instructure.com`).
- A personal Canvas API Token.

## Installation & Setup

1. Clone or download this repository.
2. Ensure you have Python 3.9+ installed.
3. Export your Canvas API token, or save it to a secure file:
   ```bash
   export CANVAS_API_TOKEN="your_token_here"
   ```

## Usage

You can use the bundled Python script directly or through Codex if installed as a skill.

### Quick Start

Create a directory where you want to store your Canvas data and run the sync script:

```bash
mkdir -p my-canvas-data
python scripts/sync_canvas.py \
  --base-url https://your-institution.instructure.com \
  --out my-canvas-data \
  --download-files
```

By default, the script will sync all active enrolled courses. 

### Syncing Specific Courses

To sync only specific course IDs, use the `--course-id` argument multiple times:

```bash
python scripts/sync_canvas.py \
  --base-url https://your-institution.instructure.com \
  --out my-canvas-data \
  --course-id 12345 \
  --course-id 67890
```

### Options

Run `python scripts/sync_canvas.py --help` for a full list of options:

- `--base-url`: **(Required)** Canvas base URL.
- `--out`: **(Required)** Output sync directory.
- `--token`: Canvas API token (prefer environment variable `CANVAS_API_TOKEN` or `--token-file`).
- `--token-file`: Path to a file containing the Canvas API token.
- `--course-id`: Specific course ID to sync.
- `--download-files`: Download course files binary payloads.
- `--no-assignment-details`: Skip fetching full assignment detail JSON.
- `--no-page-details`: Skip fetching full page detail JSON.
- `--no-commit`: Do not run `git commit` after sync.
- `--commit-message`: Provide a custom git commit message.

## Output Structure

The tool outputs a normalized directory structure:

```text
my-canvas-data/
  _changes/
    latest.md                  # Summary report of what changed during the last sync
    sync-YYYYMMDD-HHMMSS.md    # Historical sync reports
  _state/
    snapshot_index.json        # Internal hash index for change detection
  courses/
    <course-id>/
      course.json              # Course details and syllabus
      assignments.json
      assignments/             # Detailed JSON for individual assignments
      announcements.json
      pages.json
      pages/                   # Detailed JSON for individual pages
      quizzes.json
      files.json
      files/                   # Downloaded binary files
      modules.json
      modules/                 # Detailed module items
  index.json                   # Top-level index of synced courses
```

## Security Best Practices

- Treat Canvas API tokens as highly sensitive secrets.
- Never commit the token to version control.
- If using `--token-file`, ensure the file has strict permissions (`chmod 600`).
