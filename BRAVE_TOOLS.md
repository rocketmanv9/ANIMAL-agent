# BRAVE_TOOLS.md

Quick local intel + decision support using Brave Search API.

## Scripts
- `tools/local_intel.py`
- `tools/decision_support.py`

## Setup (for local script execution)
Set environment variable in your shell:

```bash
export BRAVE_API_KEY="<your_brave_api_key>"
```

## Usage
```bash
# Local intel
python3 tools/local_intel.py "best boxing gym" --near "Vancouver WA"

# Decision support
python3 tools/decision_support.py --question "best option for home internet" \
  --option "Xfinity" --option "T-Mobile Home Internet" --option "Quantum Fiber" --near "Vancouver WA"
```

## Notes
- Scripts are fast and lightweight.
- Results are directional; final judgment still needs your context.
