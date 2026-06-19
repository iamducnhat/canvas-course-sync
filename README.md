# Canvas Course Sync
![macOS](https://img.shields.io/badge/macOS-000000?style=for-the-badge&logo=apple&logoColor=white)

A lightweight, zero-setup macOS AI agent skill for syncing Instructure Canvas courses into a durable, git-backed directory.

This tool uses your Canvas API token to fetch course data (assignments, announcements, pages, quizzes, modules, and files) and normalizes it into JSON files. It generates a Markdown report of changes after each sync and optionally commits the state to a local git repository. This provides a clean, auditable history of your course updates without missing or duplicating notices.

## Features

- **Comprehensive Data Sync:** Fetches active courses, assignments (and full details), announcements, modules, pages, quizzes, and files.
- **Git-Backed Auditing:** Automatically initializes a git repository and commits changes upon each successful sync, ensuring a permanent audit trail.
- **Change Detection:** Uses content hashing to determine exactly what is new or modified.
- **Reporting:** Generates a human-readable Markdown report (`_changes/latest.md`) summarizing what changed.
- **On-Demand Syncing:** Built to be run exactly when you need to know "what's new", fetching the latest state directly from Canvas.
- **Turnitin Lite (Optional):** Evaluate your documents for plagiarism and AI-generation offline using Apple Intelligence before submitting them.
- **DeepSeek Integration (Optional):** Forward assignment details and prompts to DeepSeek for advanced AI reasoning, while the AI agent handles the API navigation.

## Prerequisites

- macOS (Intel or Apple Silicon).
- A Canvas LMS instance (e.g., `https://canvas.instructure.com`).
- A personal Canvas API Token.

## Zero-Setup Installation (For Non-Technical Users)

This tool is designed to be fully automated by your AI assistant. **You do not need to download, install, or run any commands manually!**

1. Tell your AI assistant: *"Sync my Canvas please."*
2. Provide your **Canvas Domain** and **Canvas API Token** when the AI agent asks for them.
3. Sit back and relax! 

**Behind the Scenes:** The AI agent will automatically detect if the syncing engine is missing. If so, it downloads the pre-compiled standalone binary directly from this repository's [Releases](https://github.com/iamducnhat/canvas-course-sync/releases) page, securely encrypts your token using your machine's hardware MAC address, and runs the sync.

*For advanced users: If you want to run it manually without an AI assistant, you can download the binary from the Releases page, run `chmod +x sync_canvas`, and execute it via Terminal.*

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

### Turnitin Lite (Optional Plagiarism Detection)

If you are using an Apple Silicon Mac running macOS 15.0 or later, the AI agent can use **Turnitin Lite** to evaluate your documents for plagiarism and AI-generation before you submit them to Canvas. The logic for this tool is managed in a separate repository: **[iamducnhat/turnitin-lite](https://github.com/iamducnhat/turnitin-lite)**.
This tool queries the **OpenAlex Database** for real academic plagiarism checks and uses native Apple Intelligence (FoundationModels) to estimate AI probability.

**Zero-Setup Turnitin Lite Usage:**
1. Tell your AI assistant: *"Check this file for me before submission."*
2. The AI agent will automatically verify your hardware compatibility.
3. If you approve, the AI agent will download and execute the `turnitin-lite` engine locally (v2.0.0), providing you with a detailed match report, overall AI probability score, and granular sentence-level analysis (highlighting suspicious sentences as low, mid, or high).

### DeepSeek Integration (Optional)

If you prefer to use DeepSeek for reasoning (e.g., outlining assignments), this skill can route prompts to it. However, the DeepSeek logic is managed in a separate, dedicated repository to keep this tool focused on Canvas: **[iamducnhat/deepseek4free](https://github.com/iamducnhat/deepseek4free)**.

**Zero-Setup DeepSeek Usage:**
1. Just tell your AI assistant: *"Ask deepseek to outline assignment X for me"*.
2. Provide your DeepSeek token (`userToken` from chat.deepseek.com) to the AI agent when asked.
3. The AI agent will automatically download the `ask_deepseek` binary from the [iamducnhat/deepseek4free](https://github.com/iamducnhat/deepseek4free) repository in the background and execute the prompt for you!
