#!/usr/bin/env python3
"""Relink Ableton .adg (and optional .adv) SampleRefs to original audio files.

Never copies samples. Never uses a collected Samples/ folder next to the racks.
Rewrites each SampleRef FileRef Path to an absolute original under --samples.
"""
from __future__ import annotations

import argparse
import gzip
import html
import json
import re
import shutil
import sys
from pathlib import Path

AUDIO_EXTS = {".wav", ".aif", ".aiff", ".flac", ".ogg", ".mp3"}
SAMPLE_REF_RE = re.compile(r"(<SampleRef(?:\s[^>]*)?>)(.*?)(</SampleRef>)", re.DOTALL)
FILE_REF_RE = re.compile(r"(<FileRef(?:\s[^>]*)?>)(.*?)(</FileRef>)", re.DOTALL)
VALUE_RE = r'<{name} Value="([^"]*)" />'


def xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def field(block: str, name: str) -> str:
    match = re.search(VALUE_RE.format(name=name), block)
    return html.unescape(match.group(1)) if match else ""


def set_field(block: str, name: str, value: str) -> str:
    pattern = re.compile(rf'(<{name} Value=")[^"]*(" />)')
    updated, count = pattern.subn(rf"\g<1>{xml_escape(value)}\2", block, count=1)
    if count != 1:
        raise ValueError(f"could not set {name}")
    return updated


def ableton_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def filename_of(rel: str, path: str) -> str:
    src = (path or rel).replace("\\", "/")
    if not src:
        return ""
    return src.rsplit("/", 1)[-1]


def as_fs_path(value: str) -> Path | None:
    if not value:
        return None
    return Path(value.replace("/", "\\"))


def under_any(path: Path, roots: list[Path]) -> bool:
    resolved = path.resolve()
    for root in roots:
        try:
            resolved.relative_to(root.resolve())
            return True
        except (OSError, ValueError):
            continue
    return False


def collected_sample_roots(racks: Path, extra: list[Path] | None = None) -> list[Path]:
    """Ableton collect layout: Samples/ sitting next to .adg files, plus --exclude."""
    roots: list[Path] = []
    seen: set[str] = set()

    def add(path: Path) -> None:
        if not path.exists():
            return
        key = str(path.resolve()).lower()
        if key not in seen:
            seen.add(key)
            roots.append(path)

    add(racks / "Samples")
    for preset in racks.rglob("*.adg"):
        add(preset.parent / "Samples")
    for path in extra or []:
        add(path)
    return roots


def existing_target(
    rel: str,
    abs_path: str,
    samples: Path,
    skip_roots: list[Path],
) -> Path | None:
    """Keep a path only if it already is the original under --samples.

    Never treat a file next to the .adg (including collected Samples/) as ok.
    """
    candidates: list[Path] = []
    parsed = as_fs_path(abs_path)
    if parsed:
        candidates.append(parsed)
    rel_path = as_fs_path(rel)
    if rel_path is not None:
        candidates.append(samples / rel_path)
    for candidate in candidates:
        try:
            if (
                candidate.is_file()
                and under_any(candidate, [samples])
                and not under_any(candidate, skip_roots)
            ):
                return candidate
        except OSError:
            continue
    return None


def index_audio(root: Path, skip_roots: list[Path]) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTS:
            continue
        if under_any(path, skip_roots):
            continue
        index.setdefault(path.name.lower(), []).append(path)
    return index


def pick_match(filename: str, rel: str, abs_path: str, index: dict[str, list[Path]]) -> tuple[Path | None, str | None]:
    candidates = index.get(filename.lower(), [])
    if not candidates:
        return None, f"missing:{filename}"
    if len(candidates) == 1:
        return candidates[0], None
    old = (rel or abs_path).replace("\\", "/")
    old_parts = {part.lower() for part in Path(old).parts if part not in {".", "/", "\\"}}
    scored: list[tuple[int, Path]] = []
    for candidate in candidates:
        score = len(old_parts & {part.lower() for part in candidate.parts})
        scored.append((score, candidate))
    scored.sort(key=lambda item: (-item[0], str(item[1]).lower()))
    if scored[0][0] == 0 or (len(scored) > 1 and scored[0][0] == scored[1][0]):
        locations = "; ".join(str(path) for path in candidates)
        return None, f"conflict:{filename} -> {locations}"
    return scored[0][1], None


def rewrite_file_ref(
    inner: str,
    samples: Path,
    index: dict[str, list[Path]],
    skip_roots: list[Path],
) -> tuple[str, str]:
    """Return (new_inner, status) where status is ok|rewritten|missing|conflict|empty."""
    rel = field(inner, "RelativePath")
    abs_path = field(inner, "Path")
    name = filename_of(rel, abs_path)
    if not name or Path(name).suffix.lower() not in AUDIO_EXTS:
        return inner, "empty"
    if existing_target(rel, abs_path, samples, skip_roots):
        return inner, "ok"
    match, error = pick_match(name, rel, abs_path, index)
    if match is None:
        return inner, error or f"missing:{name}"
    if under_any(match, skip_roots):
        return inner, f"missing:{name}"
    size = str(match.stat().st_size)
    updated = inner
    updated = set_field(updated, "RelativePathType", "3")
    updated = set_field(updated, "RelativePath", "")
    updated = set_field(updated, "Path", ableton_path(match))
    updated = set_field(updated, "OriginalFileSize", size)
    return updated, "rewritten"


def rewrite_xml(
    xml: str,
    adg: Path,
    samples: Path,
    index: dict[str, list[Path]],
    skip_roots: list[Path],
) -> tuple[str, dict[str, int], list[str]]:
    counts = {"ok": 0, "rewritten": 0, "empty": 0}
    problems: list[str] = []

    def repl_sample(match: re.Match[str]) -> str:
        open_tag, body, close_tag = match.group(1), match.group(2), match.group(3)
        file_match = FILE_REF_RE.search(body)
        if not file_match:
            return match.group(0)
        new_inner, status = rewrite_file_ref(
            file_match.group(2), samples, index, skip_roots
        )
        if status in counts:
            counts[status] += 1
        else:
            problems.append(f"{adg.name}: {status}")
        if new_inner == file_match.group(2):
            return match.group(0)
        start, end = file_match.span(2)
        new_body = body[:start] + new_inner + body[end:]
        return f"{open_tag}{new_body}{close_tag}"

    return SAMPLE_REF_RE.sub(repl_sample, xml), counts, problems


def read_preset(path: Path) -> tuple[bytes, bool]:
    raw = path.read_bytes()
    if raw[:2] == b"\x1f\x8b":
        return gzip.decompress(raw), True
    return raw, False


def write_preset(path: Path, xml: str, gzipped: bool) -> None:
    payload = xml.encode("utf-8")
    if gzipped:
        payload = gzip.compress(payload, mtime=0)
    path.write_bytes(payload)


def collect_presets(racks: Path, include_adv: bool) -> list[Path]:
    patterns = ["*.adg"]
    if include_adv:
        patterns.append("*.adv")
    found: list[Path] = []
    for pattern in patterns:
        found.extend(racks.rglob(pattern))
    return sorted({path.resolve() for path in found if path.is_file()})


def delete_collected_samples(skip_roots: list[Path]) -> list[str]:
    """Delete collected Samples/ dumps that sit next to .adg files. Never originals."""
    deleted: list[str] = []
    for root in skip_roots:
        resolved = root.resolve()
        if resolved.name.lower() != "samples" or not resolved.is_dir():
            continue
        try:
            siblings = list(resolved.parent.iterdir())
        except OSError:
            continue
        if not any(item.is_file() and item.suffix.lower() == ".adg" for item in siblings):
            continue
        shutil.rmtree(resolved)
        deleted.append(str(resolved))
    return deleted


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--racks", required=True, help="Folder containing broken .adg drum racks")
    parser.add_argument("--samples", required=True, help="Root folder of original sample files")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Extra collected-copy folder to skip (repeatable). Sibling Samples/ next to .adg files is always skipped.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    parser.add_argument("--backup", action="store_true", help="Copy each rewritten preset to *.adg.bak first")
    parser.add_argument("--include-adv", action="store_true", help="Also relink .adv instrument presets")
    parser.add_argument(
        "--delete-collected",
        action="store_true",
        help="After writing, delete <racks>/Samples (collected copies, never originals)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    racks = Path(args.racks).expanduser()
    samples = Path(args.samples).expanduser()
    if not racks.is_dir():
        print(json.dumps({"ok": False, "error": f"racks folder not found: {racks}"}))
        return 2
    if not samples.is_dir():
        print(json.dumps({"ok": False, "error": f"samples folder not found: {samples}"}))
        return 2

    extras = [Path(item).expanduser() for item in args.exclude]
    skip_roots = collected_sample_roots(racks, extras)
    samples_res = samples.resolve()
    if under_any(samples, skip_roots) or samples_res in {path.resolve() for path in skip_roots}:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": (
                        "samples folder is a collected Samples/ tree next to the racks; "
                        "pass the original pack root instead"
                    ),
                }
            )
        )
        return 2

    presets = collect_presets(racks, args.include_adv)
    index = index_audio(samples, skip_roots)
    if not presets:
        print(json.dumps({"ok": False, "error": f"no .adg files under {racks}"}))
        return 2
    if not index:
        print(json.dumps({"ok": False, "error": f"no original audio files under {samples}"}))
        return 2

    files_rewritten = 0
    totals = {"ok": 0, "rewritten": 0, "empty": 0}
    problems: list[str] = []
    changed_files: list[str] = []

    for preset in presets:
        try:
            xml_bytes, gzipped = read_preset(preset)
            xml = xml_bytes.decode("utf-8")
        except (OSError, gzip.BadGzipFile, UnicodeDecodeError) as exc:
            problems.append(f"{preset.name}: unreadable ({exc})")
            continue
        try:
            new_xml, counts, file_problems = rewrite_xml(
                xml, preset, samples, index, skip_roots
            )
        except ValueError as exc:
            problems.append(f"{preset.name}: {exc}")
            continue
        problems.extend(file_problems)
        for key, value in counts.items():
            totals[key] += value
        if counts["rewritten"] and new_xml != xml:
            files_rewritten += 1
            changed_files.append(str(preset))
            if not args.dry_run:
                if args.backup:
                    bak = preset.with_suffix(preset.suffix + ".bak")
                    if not bak.exists():
                        bak.write_bytes(preset.read_bytes())
                write_preset(preset, new_xml, gzipped)

    if totals["rewritten"] + totals["ok"] == 0:
        problems.append(
            "no SampleRef audio paths matched; XML may use an older RelativePathElement schema"
        )

    collected_deleted: list[str] = []
    if args.delete_collected and not args.dry_run and not problems:
        collected_deleted = delete_collected_samples(skip_roots)

    result = {
        "ok": len(problems) == 0,
        "dry_run": bool(args.dry_run),
        "racks": str(racks.resolve()),
        "samples": str(samples.resolve()),
        "skipped_collected": [str(path.resolve()) for path in skip_roots],
        "indexed_audio": sum(len(paths) for paths in index.values()),
        "preset_files": len(presets),
        "files_rewritten": files_rewritten,
        "refs_rewritten": totals["rewritten"],
        "refs_already_ok": totals["ok"],
        "empty_pads": totals["empty"],
        "collected_deleted": collected_deleted,
        "problems": problems,
        "changed_files": changed_files,
    }
    print(json.dumps(result, indent=2))
    if problems:
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 — keep stdout JSON-only for the agent
        print(json.dumps({"ok": False, "error": str(exc)}))
        raise SystemExit(1)
