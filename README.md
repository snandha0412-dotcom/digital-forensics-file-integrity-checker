# Digital Forensics File Integrity Checker

A beginner-friendly Python project that creates SHA-256 hashes for files and compares them with a trusted baseline to report files that are **added**, **modified**, or **missing**.

> **Purpose:** defensive file-integrity monitoring and digital-forensics learning. Run it only on files and folders you own or are authorized to examine. This tool does not recover deleted data or prove who changed a file.

## Features

- Build a JSON baseline containing file paths, sizes, modification times, and SHA-256 hashes.
- Verify a folder against a saved baseline.
- Report `ADDED`, `MODIFIED`, and `MISSING` files.
- Skip the baseline/report output files if they are inside the scanned folder.
- Optional JSON report output.
- Unit tests using Python's standard library; no third-party dependencies required.

## Requirements

- Python 3.9+
- Git (for uploading to GitHub)

## Project structure

```text
digital_forensics_file_integrity_checker/
├── data/
│   └── sample_files/
│       └── evidence_note.txt
├── reports/
│   └── .gitkeep
├── tests/
│   └── test_integrity_checker.py
├── .gitignore
├── integrity_checker.py
├── main.py
├── requirements.txt
└── README.md
```

## Quick start

Open a terminal in this folder.

### 1. Create a baseline

```bash
python main.py baseline data/sample_files --baseline baseline.json
```

### 2. Verify the folder

```bash
python main.py verify data/sample_files --baseline baseline.json --report reports/verification.json
```

The first verification should report all files as unchanged.

### 3. Test detection

Edit `data/sample_files/evidence_note.txt`, then run the verify command again. It should report that file as `MODIFIED`.

Add a new text file in `data/sample_files/` and verify again to see `ADDED`. Delete a sample file and verify to see `MISSING`.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Example output

```text
Status: CLEAN
Checked files: 1
Added: 0 | Modified: 0 | Missing: 0
```

If changes are found, the status is `CHANGES DETECTED` and the report lists the affected relative paths.

## How it works

1. Walks the target directory recursively.
2. Computes each file's SHA-256 digest in chunks.
3. Stores metadata in a JSON baseline.
4. Recomputes hashes and compares the current inventory with the baseline.

A hash can show that file contents differ from a prior baseline. It does not establish intent, identity, or a complete chain of custody. For real investigations, preserve original evidence, document collection steps, work on copies, and use validated forensic tools and procedures.

## GitHub upload

Create an empty repository on GitHub, for example `digital-forensics-file-integrity-checker`, then run:

```bash
git init
git add .
git commit -m "Add digital forensics file integrity checker"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/digital-forensics-file-integrity-checker.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username. Never commit private evidence, personal data, passwords, API keys, or confidential reports.

## License

MIT — see `LICENSE`.
