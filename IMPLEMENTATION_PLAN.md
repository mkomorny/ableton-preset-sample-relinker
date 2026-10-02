# Implementation Plan: ADG Sample Relink

This document tracks planned, in-progress, and completed work for the **ADG Sample Relink** skill. It persists across all version passes.

---

## Completed Work

### v1.0.0 — Initial Release (2026-09-24)
- [x] **Core Relink Engine (`scripts/relink_adg_samples.py`)**: Authored python-based gzipped-XML parser and retargeter for Ableton Live 11/12 `.adg` Drum Rack files (and optional `.adv` instruments). (✅ done in v1.0.0)
- [x] **Zero-Copy / Anti-Duplication Guardrail**: Enforced strict policy that audio files are NEVER copied into sibling folders or collected; `SampleRef` paths are retargeted directly to original audio roots. (✅ done in v1.0.0)
- [x] **Collected Folder Pruning**: Built `--delete-collected` routine to eliminate orphaned sibling `Samples/` dumps after successful writes. (✅ done in v1.0.0)
- [x] **XML & Character Entity Handling**: Built unescaping routines (`&amp;` -> `&`, etc.) to guarantee accurate filename matching against real filesystems. (✅ done in v1.0.0)
- [x] **Safety & Dry-Run Modes**:
  - [x] Comprehensive `--dry-run` inspection mode reporting retarget candidates without touching files. (✅ done in v1.0.0)
  - [x] Automated sibling `.bak` file generation on write passes. (✅ done in v1.0.0)
- [x] **Path Disambiguation Heuristic**: Subpath overlap scoring to resolve duplicate filenames within complex sample pack directory hierarchies. (✅ done in v1.0.0)
- [x] **Tri-Platform Deployment**: Established canonical skill in `.agents/skills/adg-sample-relink` with NTFS directory junctions to `.claude/skills`, `.grok/skills`, and `.gemini/config/skills`. (✅ done in v1.0.0)
- [x] **Documentation & Versioning**: Authored `SKILL.md`, standardized `HOW_TO_USE.txt`, `README.md`, and permanent `App Changes Tracker.html`. (✅ done in v1.0.0)

---

## Planned Future Work

- [ ] **Live 9/10 Schema Support**: Support legacy string FileRefs using `RelativePathElement` + `Name` nested schema.
- [ ] **Ableton ALS Project Relinking**: Extend retargeting engine to scan and repair missing audio clips within full `.als` project files.
- [ ] **Fuzzy Filename Matching**: Optional fuzzy matching for sample files with truncated extensions or slight name variations.
