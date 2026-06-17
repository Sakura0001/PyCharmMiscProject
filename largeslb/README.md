# LargeSLB Toolkit

This directory contains LargeSLB trigger scripts, fuzz tools, SQL cases, docs, tests, and packaged deliverables.

## Layout

| Path | Purpose |
|------|---------|
| `largeslb_fuzz.py` | Original LargeSLB fuzz runner |
| `largeslb_fuzz_extreme.py` | Extreme/sub-2MB concurrent burst fuzz runner |
| `largeslb_console.py` | Web console for launching and observing fuzz runs |
| `requirements-largeslb-fuzz.txt` | Python dependencies |
| `sql/` | Standalone SQL scripts and 30 TC SQL cases |
| `docs/` | Usage docs, changelogs, test plans, mind maps, and source references |
| `dist/` | Packaged `.tar.gz` / `.zip` artifacts |
| `tests/` | Unit tests |

## Recommended Sub-2MB Burst Run

```bash
python3.7 -u largeslb_fuzz_extreme.py \
  --primary-dsn 'mysql://root:password@primary-host:3306/testdb?charset=utf8mb4' \
  --readonly-dsn 'mysql://root:password@readonly-host:3306/testdb?charset=utf8mb4' \
  --state-dir "./state-sub2m-burst-$(date +%Y%m%d-%H%M%S)" \
  --run-id "sub2m-burst-$(date +%Y%m%d-%H%M%S)" \
  --sub2m-concurrent-burst \
  --sub2m-target-bytes 1835008 \
  --workers 32 \
  --bucket-count 1 \
  --rows-per-bucket 8192 \
  --target-fields longtext_col \
  --readonly-check-rate 0 \
  --engine-metric-interval 5 \
  --replica-poll-interval 2 \
  --duration 2h
```

## Verification

```bash
python3 -m unittest discover -s tests
python3 -m py_compile largeslb_fuzz.py largeslb_fuzz_extreme.py largeslb_console.py
```
