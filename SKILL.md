---
name: adg-sample-relink
description: Relink broken Ableton Drum Rack presets (.adg) so each pad always points at the original sample files. Never copies audio into a folder with the drum racks and never uses a collected Samples/ folder next to the racks. Use when the user asks to fix drum rack paths, relink adg samples, repair offline Simpler pads, delete collected Samples after relink, gives a folder of broken .adg racks plus a sample pack root, or runs /adg-sample-relink.
---

# ADG Sample Relink

**This skill ALWAYS uses the original sample file paths. It NEVER copies audio files into a folder with the drum racks (no `Samples/` collection, no duplication).**

Ableton `.adg` Drum Racks are gzipped XML. Pads do not embed audio. Each Simpler `SampleRef` stores a path. Packs often save `Samples/<kit-name>/<file>.wav` next to the rack without actually copying those files, so Live shows Offline.

This skill retargets those refs **exclusively** to the original WAVs (or AIF/FLAC/etc.) under the user-provided sample root. It never copies samples. It never treats `<racks>/Samples` as originals.

## Required inputs

Ask for both if either is missing. Do not guess a pack from a similar name.

1. **Racks folder** — directory of broken `.adg` files (recurse into subfolders).
2. **Samples folder** — root of the original audio (recurse; match by filename).

If the user says samples are "in the same directory" as the racks, that is the pack folder with the original one-shots (often the parent of a `* Drumkit` folder). It is never `<racks>/Samples`. If the named samples path is that collected tree, pass the pack root instead.

## Run

Resolve `<skill_dir>` to the directory of this `SKILL.md`. Do not rewrite XML by hand. The script overwrites `.adg` files in place. Never copy or collect audio next to the racks.

If the user asked to preview, or either folder is uncertain, dry-run first:

```bash
python "<skill_dir>/scripts/relink_adg_samples.py" --racks "<racks-folder>" --samples "<samples-folder>" --dry-run
```

When both folders are named and the user asked to fix, write with backups and delete collected copies:

```bash
python "<skill_dir>/scripts/relink_adg_samples.py" --racks "<racks-folder>" --samples "<samples-folder>" --backup --delete-collected
```

Pass `--exclude "<collected-folder>"` if the user names an extra copy to skip. Sibling `Samples/` next to `.adg` files is always skipped. Pass `--include-adv` only when the user also wants `.adv` instrument presets relinked.

## What the script does

- Index audio under the samples folder (`.wav`, `.aif`, `.aiff`, `.flac`, `.ogg`, `.mp3`). Skip every `Samples/` folder that sits next to `.adg` files, plus any `--exclude` path. Originals that live inside the drumkit folder (stems, instrument folders) are kept; only the collected `Samples/` dump is skipped.
- Unescape XML entities in stored names (`&amp;` → `&`) before matching.
- For each `.adg` `SampleRef` FileRef: if the current Path already exists **under the original samples folder** and is not under a skipped collected `Samples/`, leave it.
- Otherwise match the filename under the samples folder and write `RelativePathType=3`, empty `RelativePath`, the original file's absolute `Path` with forward slashes, and `OriginalFileSize`. Never copy, collect, or write the audio next to the racks.
- First `FileRef` inside each `SampleRef` is the live pad path, including `<SampleRef Id="...">`. Leave nested `OriginalFileRef` alone.
- Live 11/12 string FileRefs only (`Path` / `RelativePath` values). Older `RelativePathElement` + `Name` schema is not rewritten.
- `--delete-collected` removes those sibling `Samples/` dumps after a write (only folders next to `.adg` files). Always pass it on a real write. Do not pass it on a dry-run.
- Print one JSON object to stdout (`collected_deleted` is the removed paths). If `preset_files` > 0 and `refs_rewritten` + `refs_already_ok` is 0, treat it as failure (schema miss), not success.

Duplicate filenames: pick the candidate whose path parts overlap the old relative path. If still tied, report `conflict:` and skip that ref.

## After the script

Report in plain language: files rewritten, refs rewritten, already-ok refs, missing/conflict names, whether collected `Samples/` was deleted.

If refs were rewritten, tell the user to drag the `.adg` in again (or File → Manage Files → Locate) if Live still shows Offline from an earlier load.

If `problems` is non-empty, list those filenames. Do not invent replacements.

## Do not (STRICT RULES — ALWAYS ENFORCED)

- **NEVER** copy, collect, or duplicate any samples into a `Samples/` folder next to the drum racks.
- **ALWAYS** use the original sample paths provided by the user (typically the pack root, not a `* Drumkit` subfolder or any collected `Samples/`).
- Never use `<racks>/Samples` as `--samples` or as an already-ok target.
- Never leave a collected `<racks>/Samples` folder after a successful write (the script deletes it when `--delete-collected` is used).
- Never guess paths. Always ask for both racks folder and original samples folder if unclear.
- Load Ableton only if the user explicitly asks to test a rack in the open Set.
