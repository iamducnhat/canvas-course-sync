# Canvas Course Sync
![macOS](https://img.shields.io/badge/macOS-000000?style=for-the-badge&logo=apple&logoColor=white)

A lightweight, zero-setup macOS Codex skill for syncing Instructure Canvas courses into a durable, git-backed directory.

This tool uses your Canvas API token to fetch course data (assignments, announcements, pages, quizzes, modules, and files) and normalizes it into JSON files. It generates a Markdown report of changes after each sync and optionally commits the state to a local git repository. This provides a clean, auditable history of your course updates without missing or duplicating notices.

## Features

- **Comprehensive Data Sync:** Fetches active courses, assignments (and full details), announcements, modules, pages, quizzes, and files.
- **Git-Backed Auditing:** Automatically initializes a git repository and commits changes upon each successful sync, ensuring a permanent audit trail.
- **Change Detection:** Uses content hashing to determine exactly what is new or modified.
- **Reporting:** Generates a human-readable Markdown report (`_changes/latest.md`) summarizing what changed.
- **On-Demand Syncing:** Built to be run exactly when you need to know "what's new", fetching the latest state directly from Canvas.
- **Turnitin Lite (Optional):** Evaluate your documents for plagiarism and AI-generation offline using Apple Intelligence before submitting them.
- **DeepSeek Integration (Optional):** Forward assignment details and prompts to DeepSeek for advanced AI reasoning, while Codex handles the API navigation.

## Prerequisites

- macOS (Intel or Apple Silicon).
- A Canvas LMS instance (e.g., `https://canvas.instructure.com`).
- A personal Canvas API Token.

## Zero-Setup Installation (For Non-Technical Users)

This tool is designed to be fully automated by your Codex AI assistant. **You do not need to download, install, or run any commands manually!**

1. Tell your Codex: *"Sync my Canvas please."*
2. Provide your **Canvas Domain** and **Canvas API Token** when Codex asks for them.
3. Sit back and relax! 

**Behind the Scenes:** Codex will automatically detect if the syncing engine is missing. If so, it downloads the pre-compiled standalone binary directly from this repository's [Releases](https://github.com/iamducnhat/canvas-course-sync/releases) page, securely encrypts your token using your machine's hardware MAC address, and runs the sync.

*For advanced users: If you want to run it manually without Codex, you can download the binary from the Releases page, run `chmod +x sync_canvas`, and execute it via Terminal.*

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

If you are using an Apple Silicon Mac running macOS 15.0 or later, Codex can use **Turnitin Lite** to evaluate your documents for plagiarism and AI-generation before you submit them to Canvas. 
This tool queries the **OpenAlex Database** for real academic plagiarism checks and uses native Apple Intelligence (FoundationModels) to estimate AI probability.

**Zero-Setup Turnitin Lite Usage:**
1. Tell Codex: *"Kiểm tra file này giúp tôi trước khi nộp."*
2. Codex will automatically verify your hardware compatibility.
3. If you approve, Codex will download and execute the `turnitin-lite` engine locally, providing you with a detailed match report and AI probability score.

### DeepSeek Integration (Optional)

If you prefer to use DeepSeek for reasoning (e.g., outlining assignments), this skill can route prompts to it. However, the DeepSeek logic is managed in a separate, dedicated repository to keep this tool focused on Canvas: **[iamducnhat/deepseek4free](https://github.com/iamducnhat/deepseek4free)**.

**Zero-Setup DeepSeek Usage:**
1. Just tell Codex: *"Bảo deepseek lên cái sườn cho bài tập X hộ tôi"*.
2. Provide your DeepSeek token (`userToken` from chat.deepseek.com) to Codex when asked.
3. Codex will automatically download the `ask_deepseek` binary from the [iamducnhat/deepseek4free](https://github.com/iamducnhat/deepseek4free) repository in the background and execute the prompt for you!
