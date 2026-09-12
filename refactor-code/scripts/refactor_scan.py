#!/usr/bin/env python3
"""Scan a repository for large source files, refactor smell hints, and tooling hints."""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
from pathlib import Path
from typing import Iterable


DEFAULT_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".mjs",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scss",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
}

IGNORE_DIRS = {
    ".git",
    ".hg",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "vendor",
}

BRACE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".mjs",
    ".php",
    ".rs",
    ".swift",
    ".ts",
    ".tsx",
}

FUNCTION_START_RE = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?(?:function\s+\w+|def\s+\w+|"
    r"(?:public|private|protected|static|final|override|internal|open|\s)*"
    r"[\w<>\[\], ?:.]+\s+\w+\s*\(|\w+\s*[:=]\s*(?:async\s*)?\([^)]*\)\s*=>)"
)
CLASS_START_RE = re.compile(
    r"^\s*(?:export\s+)?(?:abstract\s+|final\s+|open\s+|public\s+|private\s+|protected\s+)*"
    r"(?:class|interface|struct|enum)\s+\w+"
)
PARAM_RE = re.compile(r"\(([^()]*)\)")
STRING_RE = re.compile(r"(['\"])(?:\\.|(?!\1).)*\1")
NUMBER_RE = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])")
MEMBER_ACCESS_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\.")

SMELL_LIMITS = {
    "long_method_lines": 100,
    "large_class_lines": 300,
    "long_parameter_count": 4,
    "duplicate_block_lines": 6,
    "magic_number_count": 8,
    "feature_envy_member_reads": 10,
}


def iter_source_files(root: Path, extensions: set[str]) -> Iterable[Path]:
    for current, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in IGNORE_DIRS]
        current_path = Path(current)
        for filename in filenames:
            path = current_path / filename
            if path.suffix.lower() in extensions:
                yield path


def count_lines(path: Path) -> int:
    try:
        with path.open("rb") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}


def strip_strings(line: str) -> str:
    return STRING_RE.sub('""', line)


def normalize_for_duplicates(line: str) -> str:
    stripped = strip_strings(line).strip()
    if not stripped or stripped.startswith(("#", "//", "*", "/*", "*/")):
        return ""
    stripped = NUMBER_RE.sub("0", stripped)
    normalized = re.sub(r"\s+", " ", stripped)
    if not re.search(r"[A-Za-z_]", normalized):
        return ""
    return normalized


def is_control_line(line: str) -> bool:
    return line.lstrip().startswith(("for ", "if ", "while ", "with ", "except ", "return "))


def make_issue(kind: str, line: int, message: str, **extra: object) -> dict:
    return {"type": kind, "line": line, "message": message, **extra}


def count_params(line: str) -> int:
    match = PARAM_RE.search(line)
    if not match:
        return 0
    params = [
        param.strip()
        for param in match.group(1).split(",")
        if param.strip() and param.strip() not in {"self", "this"}
    ]
    return len(params)


def brace_block_end(lines: list[str], start_index: int) -> int:
    depth = 0
    seen_open = False
    for index in range(start_index, len(lines)):
        line = strip_strings(lines[index])
        depth += line.count("{")
        if "{" in line:
            seen_open = True
        depth -= line.count("}")
        if seen_open and depth <= 0:
            return index
    return start_index


def indent_block_end(lines: list[str], start_index: int) -> int:
    start_line = lines[start_index]
    start_indent = len(start_line) - len(start_line.lstrip())
    end_index = start_index
    for index in range(start_index + 1, len(lines)):
        line = lines[index]
        if not line.strip():
            end_index = index
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= start_indent:
            break
        end_index = index
    return end_index


def block_end(lines: list[str], start_index: int, extension: str) -> int:
    if extension in BRACE_EXTENSIONS or "{" in lines[start_index]:
        return brace_block_end(lines, start_index)
    return indent_block_end(lines, start_index)


def line_preview(line: str) -> str:
    preview = line.strip()
    return preview[:117] + "..." if len(preview) > 120 else preview


def detect_duplicate_blocks(lines: list[str]) -> list[dict]:
    block_size = SMELL_LIMITS["duplicate_block_lines"]
    blocks: dict[tuple[str, ...], list[int]] = collections.defaultdict(list)
    normalized = [normalize_for_duplicates(line) for line in lines]
    for index in range(0, max(0, len(normalized) - block_size + 1)):
        block = tuple(normalized[index : index + block_size])
        if all(block):
            blocks[block].append(index + 1)

    duplicates = []
    for block, starts in blocks.items():
        if len(starts) > 1:
            duplicates.append(
                make_issue(
                    "duplicated_code",
                    starts[0],
                    f"{block_size}-line normalized block repeats at lines {starts[:5]}",
                )
            )
    return duplicates[:10]


def detect_magic_numbers(lines: list[str]) -> list[dict]:
    hits = []
    ignored = {"-1", "0", "1", "2", "100", "1000"}
    for index, line in enumerate(lines, start=1):
        code = strip_strings(line)
        if re.search(r"\b(?:const|enum|static readonly|readonly)\b", code) or re.search(
            r"^\s*['\"]?\w+['\"]?\s*:", line
        ):
            continue
        for match in NUMBER_RE.finditer(code):
            value = match.group(0)
            if value not in ignored:
                hits.append({"line": index, "value": value, "preview": line_preview(line)})
                break
    if len(hits) < SMELL_LIMITS["magic_number_count"]:
        return []
    return [
        make_issue(
            "magic_numbers",
            hits[0]["line"],
            f"{len(hits)} numeric literals outside obvious constant declarations",
            examples=hits[:5],
        )
    ]


def detect_member_envy(lines: list[str], start_index: int, end_index: int) -> list[dict]:
    counts: collections.Counter[str] = collections.Counter()
    for line in lines[start_index : end_index + 1]:
        for receiver in MEMBER_ACCESS_RE.findall(strip_strings(line)):
            if receiver not in {"self", "this", "super", "console", "Math", "Date"}:
                counts[receiver] += 1
    if not counts:
        return []
    receiver, count = counts.most_common(1)[0]
    if count < SMELL_LIMITS["feature_envy_member_reads"]:
        return []
    return [
        make_issue(
            "feature_envy",
            start_index + 1,
            f"function reads '{receiver}.' {count} times; check whether behavior belongs closer to that object",
        )
    ]


def detect_smells(path: Path, root: Path) -> list[dict]:
    lines = read_lines(path)
    if not lines:
        return []

    extension = path.suffix.lower()
    issues = []
    issues.extend(detect_duplicate_blocks(lines))
    issues.extend(detect_magic_numbers(lines))

    for index, line in enumerate(lines):
        if not is_control_line(line) and FUNCTION_START_RE.search(line):
            params = count_params(line)
            if params > SMELL_LIMITS["long_parameter_count"]:
                issues.append(
                    make_issue(
                        "long_parameter_list",
                        index + 1,
                        f"{params} parameters; consider a parameter object or narrower API",
                    )
                )
            end_index = block_end(lines, index, extension)
            block_lines = end_index - index + 1
            if block_lines >= SMELL_LIMITS["long_method_lines"]:
                issues.append(
                    make_issue(
                        "long_method",
                        index + 1,
                        f"{block_lines} lines; consider extracting named steps",
                    )
                )
            issues.extend(detect_member_envy(lines, index, end_index))

        if CLASS_START_RE.search(line):
            end_index = block_end(lines, index, extension)
            block_lines = end_index - index + 1
            if block_lines >= SMELL_LIMITS["large_class_lines"]:
                issues.append(
                    make_issue(
                        "large_class",
                        index + 1,
                        f"{block_lines} lines; check SRP and extract responsibilities",
                    )
                )

    for issue in issues:
        issue["path"] = str(path.relative_to(root))
    return issues[:30]


def detect_formatter_hints(root: Path) -> list[str]:
    hints: list[str] = []

    package_json = root / "package.json"
    if package_json.exists():
        scripts = read_json(package_json).get("scripts", {})
        if isinstance(scripts, dict):
            for name in ("format", "format:check", "lint", "typecheck", "test"):
                if name in scripts:
                    hints.append(f"package.json script: {name} -> {scripts[name]}")

    config_hints = {
        "pyproject.toml": "Python tooling config; inspect for black, ruff, isort, pytest",
        ".prettierrc": "Prettier config",
        ".prettierrc.json": "Prettier config",
        ".prettierrc.yml": "Prettier config",
        ".prettierrc.yaml": "Prettier config",
        "prettier.config.js": "Prettier config",
        "eslint.config.js": "ESLint config",
        ".eslintrc": "ESLint config",
        ".editorconfig": "EditorConfig formatting defaults",
        "go.mod": "Go module; use gofmt/go test",
        "Cargo.toml": "Rust crate; use cargo fmt/cargo test",
    }
    for filename, description in config_hints.items():
        if (root / filename).exists():
            hints.append(f"{filename}: {description}")

    return hints


def parse_extensions(raw: str | None) -> set[str]:
    if not raw:
        return set(DEFAULT_EXTENSIONS)
    extensions = set()
    for item in raw.split(","):
        item = item.strip().lower()
        if not item:
            continue
        extensions.add(item if item.startswith(".") else f".{item}")
    return extensions


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List source files at or above a line threshold, smell hints, and tooling hints."
    )
    parser.add_argument("root", nargs="?", default=".", help="Repository root to scan")
    parser.add_argument("--min-lines", type=int, default=1200, help="Minimum line count to report")
    parser.add_argument(
        "--extensions",
        help="Comma-separated extensions to include, such as py,ts,tsx",
    )
    parser.add_argument("--no-smells", action="store_true", help="Skip heuristic smell scan")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    extensions = parse_extensions(args.extensions)
    large_files = []
    smell_hints = []

    for path in iter_source_files(root, extensions):
        lines = count_lines(path)
        if lines >= args.min_lines:
            large_files.append(
                {
                    "path": str(path.relative_to(root)),
                    "lines": lines,
                    "extension": path.suffix.lower(),
                }
            )
        if not args.no_smells:
            smell_hints.extend(detect_smells(path, root))

    large_files.sort(key=lambda item: (-item["lines"], item["path"]))
    smell_hints.sort(key=lambda item: (item["path"], item["line"], item["type"]))
    result = {
        "root": str(root),
        "min_lines": args.min_lines,
        "large_files": large_files,
        "smell_hints": smell_hints,
        "smell_limits": SMELL_LIMITS,
        "formatter_hints": detect_formatter_hints(root),
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Repository: {result['root']}")
        print(f"Large files (>= {args.min_lines} lines):")
        if large_files:
            for item in large_files:
                print(f"  {item['lines']:>5}  {item['path']}")
        else:
            print("  none")
        print("Refactor smell hints:")
        if smell_hints:
            for item in smell_hints:
                print(f"  - {item['path']}:{item['line']} [{item['type']}] {item['message']}")
        else:
            print("  none detected")
        print("Formatter and validation hints:")
        if result["formatter_hints"]:
            for hint in result["formatter_hints"]:
                print(f"  - {hint}")
        else:
            print("  none detected")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
