# misophonia-dataset

The first large-scale, open-access binaural dataset confirmed to trigger people with misophonia

License: N/A


## Getting Started

Pre-requisites:

- Docker
- VS Code
- DevContainer Extension

## Creating the Dataset

### Trigger Sounds
1. Create a directory called data and a subdirectory metadata
2. Download FSDK50_dev, FSD50K_eval ESC50 and FOAMS datasets into data (requires ~30gb disk space)
3. Run the scripts to generate trigger examples from each dataset
4. Merge and split trigger sounds into dev and eval sets

### Control Sounds
1. Run the scripts to generate control sounds from the datasets
2. Merge and split control sounds into dev and eval sets

### Background Sounds
1. Run the scripts to generate background sounds from the datasets
2. Merge and split background sounds into dev and eval sets

### Binaural Mixing & Final Dataset
1. Run mixing script on dev directory and on eval directory to generate final train/test binaural Misophonia dataset.


## Developing

Install a package:

```bash
uv add [--dev] <package>
```
