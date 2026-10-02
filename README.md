# Ableton Preset Sample Relinker

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
