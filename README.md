# Ableton Preset Sample Relinker

[![Automated Release](https://img.shields.io/badge/release-automated_batch_pipeline-blue.svg)](https://github.com/mkomorny)
[![Pipeline Execution](https://img.shields.io/badge/dispatched_by-background_script-informational.svg)](https://github.com/mkomorny)

> [!NOTE]
> **Automated Distribution**: This repository was automatically sanitized, packaged, and published via a scheduled background batch staging pipeline. All file bundling, licensing, and repository synchronization were dispatched automatically by an automated release runner.

A zero-dependency Python systems utility for Digital Audio Workstations that inspects, repairs, and dynamically relinks broken audio sample references (`SampleRef` / `FileRef`) inside Ableton Live Drum Racks and Instrument presets (`.adg` and `.adv`).

## Problem Solved

When moving sample packs, transferring projects across machines, or organizing sample libraries, Ableton presets frequently lose track of their underlying WAV/AIFF samples, resulting in silent or offline pads. Standard DAW collection methods redundantly copy audio files, wasting gigabytes of disk space.

## Technical Design

- **Gzip XML Stream Decompression**: Ableton `.adg` and `.adv` files are gzip-compressed XML streams. This utility uncompresses, parses, modifies, and re-compresses the preset binary streams in memory without quality loss.
- **Zero Duplication**: Rewrites absolute and relative paths directly to original user sample roots without creating bloated `Samples/` clone folders.
- **Heuristic Path Reconstruction**: Matches missing sample filenames against your local sample directory tree using fuzzy token scoring and recursive filesystem indexing.
- **Zero Third-Party Dependencies**: Written entirely in pure Python standard library (`gzip`, `re`, `html`, `pathlib`, `argparse`).

## Dependencies

- **Python**: 3.8+ (Pure standard library)

## Instructions

See [INSTRUCTIONS.md](./INSTRUCTIONS.md) for batch relinking commands.

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0) - see the [LICENSE](./LICENSE) file for details.
