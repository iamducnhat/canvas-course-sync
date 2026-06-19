---
name: canvas-turnitin-lite
description: macOS-only Turnitin Lite workflow for students checking a file before Canvas submission. Use when the user asks about plagiarism, AI detection, similarity, originality, Turnitin, or checking a file before submitting to Canvas.
---

# Student Turnitin Lite for macOS

Use this macOS-only student skill to run the plugin's optional Turnitin Lite workflow for a local file. This is for pre-submission review only; do not submit anything to Canvas unless the user explicitly asks after seeing the results.

Resolve paths relative to this skill directory. In the public repository plugin layout, the shared binary folder is `../../bin/`; the Turnitin Lite executable should live at `../../bin/turnitin-lite`.

## Required Consent

Turnitin Lite must never be downloaded or run silently. If the user did not explicitly ask to run Turnitin Lite in the current request, ask:

```text
To check for plagiarism and AI, I can use Turnitin Lite, which runs offline on your Mac. Would you like me to download and run it for this file?
```

If the user says no, do not download it. Offer a manual review instead. If the user says yes or already asked to run Turnitin Lite, continue.

## Workflow

1. Confirm the file path. If no file is provided, ask which file to check.
2. Check hardware before downloading:

```bash
sysctl -n machdep.cpu.brand_string
sw_vers
```

Use Turnitin Lite only on Apple Silicon Macs running macOS 15.0 or later. If unsupported, explain that Turnitin Lite cannot run locally and perform a manual review instead.

3. Ensure the executable exists only after consent:

```bash
mkdir -p ../../bin
curl -L -o ../../bin/turnitin-lite https://github.com/iamducnhat/turnitin-lite/releases/download/v2.0.0/turnitin-lite
chmod +x ../../bin/turnitin-lite
```

4. Run the check:

```bash
../../bin/turnitin-lite <path_to_file>
```

5. Report the JSON results in plain language. Include plagiarism/similarity signals, AI probability, and sentence-level findings from `suspectedSentences` with low, mid, or high labels when present.

## Safety

- Do not upload the file to external services as part of this skill.
- Do not claim the score is an official Turnitin result.
- Do not store the checked file in the plugin directory.
- If the user later wants to submit the file to Canvas, switch to `$canvas-course-sync`, confirm the Canvas domain URL and API token setup, then use the submission flags.
