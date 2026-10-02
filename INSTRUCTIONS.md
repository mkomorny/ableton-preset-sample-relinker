# Ableton Preset Sample Relinker - Usage Guide

## Prerequisites

- **Python**: 3.8+ (No pip install required!)

---

## 1. Batch Relinking Presets

Relink a folder of `.adg` drum racks against your primary sample library root:
```bash
python scripts/relink_adg_samples.py --presets "/path/to/Drum Racks" --samples "/path/to/Audio Samples"
```

## 2. Dry Run Mode

Preview broken vs repaired paths without modifying files on disk:
```bash
python scripts/relink_adg_samples.py --presets "/path/to/Drum Racks" --samples "/path/to/Audio Samples" --dry-run
```
