#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


Json = dict[str, Any] | list[Any]


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def slug(value: str, limit: int = 90) -> str:
    value = re.sub(r"[^\w.\-() ]+", "_", value, flags=re.UNICODE).strip()
    value = re.sub(r"\s+", " ", value)
    return value[:limit].strip(" ._") or "untitled"


def stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(data: Any) -> str:
    return hashlib.sha256(stable_json(data).encode("utf-8")).hexdigest()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


class CanvasClient:
    def __init__(self, base_url: str, token: str, timeout: int = 45, polite_sleep: float = 0.05):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.polite_sleep = polite_sleep

    def url(self, path: str, params: dict[str, Any] | None = None) -> str:
        if not path.startswith("/"):
            path = "/" + path
        url = self.base_url + path
        if params:
            pairs: list[tuple[str, str]] = []
            for key, value in params.items():
                if value is None:
                    continue
                if isinstance(value, list):
                    pairs.extend((key, str(item)) for item in value)
                else:
                    pairs.append((key, str(value)))
            url += "?" + urllib.parse.urlencode(pairs)
        return url

    def request(self, url: str) -> tuple[Any, dict[str, str]]:
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Accept", "application/json")
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                    text = raw.decode("utf-8") if raw else "null"
                    return json.loads(text), {k.lower(): v for k, v in resp.headers.items()}
            except urllib.error.HTTPError as exc:
                if exc.code == 401:
                    print(f"\nERROR_CANVAS_AUTH_FAILED: Canvas API token is invalid or expired. HTTP 401.", file=sys.stderr)
                    sys.exit(1)
                if exc.code in {429, 500, 502, 503, 504} and attempt < 3:
                    time.sleep(2**attempt)
                    continue
                body = exc.read().decode("utf-8", errors="replace")[:500]
                raise RuntimeError(f"Canvas API error {exc.code} for {redact_url(url)}: {body}") from exc
            except urllib.error.URLError as exc:
                if attempt < 3:
                    time.sleep(2**attempt)
                    continue
                raise RuntimeError(f"Network error for {redact_url(url)}: {exc}") from exc
        raise RuntimeError(f"Failed request after retries: {redact_url(url)}")

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        data, _ = self.request(self.url(path, params))
        time.sleep(self.polite_sleep)
        return data

    def paged(self, path: str, params: dict[str, Any] | None = None) -> list[Any]:
        first_params = {"per_page": 100}
        if params:
            first_params.update(params)
        url = self.url(path, first_params)
        out: list[Any] = []
        while url:
            data, headers = self.request(url)
            if isinstance(data, list):
                out.extend(data)
            else:
                out.append(data)
            url = parse_next(headers.get("link", ""))
            time.sleep(self.polite_sleep)
        return out

    def download(self, url: str, path: Path) -> bool:
        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {self.token}")
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=max(self.timeout, 120)) as resp:
                    new = resp.read()
                if path.exists() and path.read_bytes() == new:
                    return False
                path.write_bytes(new)
                return True
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
        return False


def parse_next(link_header: str) -> str | None:
    for part in link_header.split(","):
        if 'rel="next"' in part:
            match = re.search(r"<([^>]+)>", part)
            if match:
                return match.group(1)
    return None


def redact_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    safe = [(k, "***" if "token" in k.lower() else v) for k, v in query]
    return urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(safe)))


def object_summary(kind: str, obj: dict[str, Any]) -> str:
    title = obj.get("name") or obj.get("title") or obj.get("display_name") or obj.get("filename") or f"{kind} {obj.get('id', '')}"
    bits = [str(title)]
    due = obj.get("due_at")
    unlock = obj.get("unlock_at")
    updated = obj.get("updated_at") or obj.get("posted_at") or obj.get("created_at")
    if due:
        bits.append(f"due {due}")
    if unlock:
        bits.append(f"unlock {unlock}")
    if updated:
        bits.append(f"updated {updated}")
    return " | ".join(bits)


def state_key(course_id: int | str, kind: str, obj: dict[str, Any]) -> str:
    return f"{course_id}:{kind}:{obj.get('id')}"


def record_change(
    state: dict[str, Any],
    changes: list[dict[str, Any]],
    course: dict[str, Any],
    kind: str,
    obj: dict[str, Any],
) -> None:
    course_id = course["id"]
    key = state_key(course_id, kind, obj)
    digest = sha256(obj)
    old = state.get("objects", {}).get(key)
    item = {
        "hash": digest,
        "kind": kind,
        "course_id": course_id,
        "course_name": course.get("name") or course.get("course_code") or str(course_id),
        "object_id": obj.get("id"),
        "updated_at": obj.get("updated_at") or obj.get("posted_at") or obj.get("created_at"),
        "summary": object_summary(kind, obj),
    }
    if not old:
        changes.append({"status": "new", **item})
    elif old.get("hash") != digest:
        changes.append({"status": "changed", "previous": old.get("summary"), **item})
    state.setdefault("objects", {})[key] = item


def git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)


def ensure_git(repo: Path) -> None:
    if not (repo / ".git").exists():
        git(["init"], repo)
        git(["config", "user.name", "Canvas Sync"], repo, check=False)
        git(["config", "user.email", "canvas-sync@local"], repo, check=False)


def commit_if_changed(repo: Path, message: str) -> bool:
    git(["add", "."], repo)
    status = git(["status", "--porcelain"], repo).stdout.strip()
    if not status:
        return False
    git(["commit", "-m", message], repo)
    return True


def get_token(args: argparse.Namespace) -> str:
    if args.token:
        return args.token.strip()
    if args.token_file:
        return Path(args.token_file).expanduser().read_text(encoding="utf-8").strip()
    env = os.environ.get("CANVAS_API_TOKEN")
    if env:
        return env.strip()
    try:
        import subprocess
        result = subprocess.run(['security', 'find-generic-password', '-a', os.environ.get('USER', ''), '-s', 'canvas_api_token', '-w'], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception:
        pass
    raise SystemExit("Missing token. Use --token, --token-file, CANVAS_API_TOKEN, or store in macOS Keychain (canvas_api_token).")


def fetch_course(client: CanvasClient, out: Path, state: dict[str, Any], changes: list[dict[str, Any]], course: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    course_id = course["id"]
    course_dir = out / "courses" / str(course_id)
    course_dir.mkdir(parents=True, exist_ok=True)
    detail = client.get(f"/api/v1/courses/{course_id}", {"include[]": ["term", "teachers", "total_students", "syllabus_body"]})
    write_json(course_dir / "course.json", detail)
    record_change(state, changes, detail, "course", detail)

    assignments = client.paged(f"/api/v1/courses/{course_id}/assignments", {"include[]": ["submission", "score_statistics"]})
    write_json(course_dir / "assignments.json", assignments)
    for assignment in assignments:
        record_change(state, changes, detail, "assignment", assignment)
        if args.assignment_details:
            try:
                full = client.get(f"/api/v1/courses/{course_id}/assignments/{assignment['id']}")
                write_json(course_dir / "assignments" / f"{assignment['id']}.json", full)
            except Exception as exc:
                changes.append({"status": "warning", "kind": "assignment_detail", "course_id": course_id, "summary": str(exc)})

    announcements = client.paged(
        f"/api/v1/courses/{course_id}/discussion_topics",
        {"only_announcements": "true", "include[]": ["sections", "sections_user_count"]},
    )
    write_json(course_dir / "announcements.json", announcements)
    for ann in announcements:
        record_change(state, changes, detail, "announcement", ann)

    modules = client.paged(f"/api/v1/courses/{course_id}/modules", {"include[]": ["items"]})
    write_json(course_dir / "modules.json", modules)
    for module in modules:
        record_change(state, changes, detail, "module", module)
        try:
            items = client.paged(f"/api/v1/courses/{course_id}/modules/{module['id']}/items")
            write_json(course_dir / "modules" / f"{module['id']}-items.json", items)
            for item in items:
                record_change(state, changes, detail, "module_item", item)
        except Exception as exc:
            changes.append({"status": "warning", "kind": "module_items", "course_id": course_id, "summary": str(exc)})

    try:
        pages = client.paged(f"/api/v1/courses/{course_id}/pages")
        write_json(course_dir / "pages.json", pages)
        for page in pages:
            record_change(state, changes, detail, "page", page)
            if args.page_details:
                try:
                    full = client.get(f"/api/v1/courses/{course_id}/pages/{page['url']}")
                    write_json(course_dir / "pages" / f"{page['url']}.json", full)
                except Exception as exc:
                    changes.append({"status": "warning", "kind": "page_detail", "course_id": course_id, "summary": str(exc)})
    except Exception as exc:
        pages = []
        changes.append({"status": "warning", "kind": "pages_sync", "course_id": course_id, "summary": str(exc)})

    try:
        quizzes = client.paged(f"/api/v1/courses/{course_id}/quizzes")
        write_json(course_dir / "quizzes.json", quizzes)
        for quiz in quizzes:
            record_change(state, changes, detail, "quiz", quiz)
    except Exception as exc:
        quizzes = []
        changes.append({"status": "warning", "kind": "quizzes_sync", "course_id": course_id, "summary": str(exc)})

    files = client.paged(f"/api/v1/courses/{course_id}/files")
    write_json(course_dir / "files.json", files)
    for file_obj in files:
        record_change(state, changes, detail, "file", file_obj)
        if args.download_files and file_obj.get("url"):
            name = f"{file_obj.get('id')}-{slug(file_obj.get('display_name') or file_obj.get('filename') or 'file')}"
            target = course_dir / "files" / name
            try:
                changed = client.download(file_obj["url"], target)
                if changed:
                    changes.append({
                        "status": "downloaded",
                        "kind": "file_binary",
                        "course_id": course_id,
                        "course_name": detail.get("name"),
                        "object_id": file_obj.get("id"),
                        "summary": str(target.relative_to(out)),
                    })
            except Exception as exc:
                changes.append({"status": "warning", "kind": "file_download", "course_id": course_id, "summary": str(exc)})

    return {
        "id": course_id,
        "name": detail.get("name"),
        "course_code": detail.get("course_code"),
        "assignments": len(assignments),
        "announcements": len(announcements),
        "modules": len(modules),
        "pages": len(pages),
        "quizzes": len(quizzes),
        "files": len(files),
    }


def write_report(out: Path, changes: list[dict[str, Any]], index: dict[str, Any], stamp: str) -> None:
    lines = [
        f"# Canvas Sync Report - {stamp}",
        "",
        f"Courses synced: {len(index['courses'])}",
        f"Objects changed/new/downloaded/warnings: {len(changes)}",
        "",
    ]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for change in changes:
        grouped.setdefault(change.get("status", "changed"), []).append(change)
    for status in ["new", "changed", "downloaded", "warning"]:
        items = grouped.get(status, [])
        if not items:
            continue
        lines.append(f"## {status.title()}")
        lines.append("")
        for item in items:
            course = item.get("course_name") or item.get("course_id") or "unknown course"
            kind = item.get("kind", "item")
            summary = item.get("summary", "")
            lines.append(f"- [{kind}] {course}: {summary}")
            if item.get("previous"):
                lines.append(f"  Previous: {item['previous']}")
        lines.append("")
    if not changes:
        lines.extend(["No new or changed Canvas objects detected.", ""])
    changes_dir = out / "_changes"
    changes_dir.mkdir(parents=True, exist_ok=True)
    report = "\n".join(lines)
    (changes_dir / "latest.md").write_text(report, encoding="utf-8")
    (changes_dir / f"sync-{stamp.replace(':', '').replace('-', '').replace('T', '-')}.md").write_text(report, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync Canvas courses into a git-backed local mirror.")
    parser.add_argument("--base-url", required=True, help="Canvas base URL, e.g. https://vinuni.instructure.com")
    parser.add_argument("--token", help="Canvas API token. Prefer CANVAS_API_TOKEN or --token-file when possible.")
    parser.add_argument("--token-file", help="Path to a file containing the Canvas API token.")
    parser.add_argument("--out", required=True, help="Output sync directory.")
    parser.add_argument("--course-id", action="append", type=int, default=[], help="Canvas course ID to sync. Repeat for multiple courses.")
    parser.add_argument("--download-files", action="store_true", help="Download course files listed by Canvas.")
    parser.add_argument("--assignment-details", action=argparse.BooleanOptionalAction, default=True, help="Fetch full assignment detail JSON.")
    parser.add_argument("--page-details", action=argparse.BooleanOptionalAction, default=True, help="Fetch full page detail JSON.")
    parser.add_argument("--no-commit", action="store_true", help="Do not git commit after sync.")
    parser.add_argument("--commit-message", help="Custom git commit message.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = get_token(args)
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    ensure_git(out)

    state_path = out / "_state" / "snapshot_index.json"
    state = read_json(state_path, {"version": 1, "objects": {}})
    state["last_started_at"] = now_utc()
    changes: list[dict[str, Any]] = []

    client = CanvasClient(args.base_url, token)
    if args.course_id:
        courses = [client.get(f"/api/v1/courses/{cid}") for cid in args.course_id]
    else:
        courses = client.paged("/api/v1/courses", {"enrollment_state": "active", "include[]": ["term", "teachers"]})
        courses = [course for course in courses if not course.get("access_restricted_by_date")]

    index = {
        "base_url": args.base_url.rstrip("/"),
        "synced_at": now_utc(),
        "courses": [],
    }
    for course in courses:
        if not course.get("id"):
            continue
        try:
            index["courses"].append(fetch_course(client, out, state, changes, course, args))
        except Exception as exc:
            changes.append({"status": "warning", "kind": "course_sync", "course_id": course.get("id"), "summary": str(exc)})

    state["last_completed_at"] = now_utc()
    write_json(state_path, state)
    write_json(out / "index.json", index)
    stamp = dt.datetime.now().replace(microsecond=0).isoformat(timespec="seconds")
    write_report(out, changes, index, stamp)

    committed = False
    if not args.no_commit:
        message = args.commit_message or f"canvas sync {stamp}"
        committed = commit_if_changed(out, message)

    print(json.dumps({
        "out": str(out),
        "courses": len(index["courses"]),
        "changes": len(changes),
        "report": str(out / "_changes" / "latest.md"),
        "committed": committed,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
