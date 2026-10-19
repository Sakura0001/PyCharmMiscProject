# Primary-key type-upgrade concurrency audit

**Result:** PASS

- **Batch ID:** `2026-10-19-type-upgrade-primary-key-concurrency-v1`
- **Transitions:** 107
- **Virtual scenarios:** 946944
- **Smoke cases:** 107
- **CHAR/VARCHAR Instant matrix:** PASS
- **TEXT/BLOB prefix matrix:** PASS
- **Local COPY smoke:** 107 results, ALL PASS
- **During-DDL evidence:** 10 results, 10 overlaps, ALL PASS
- **Across-DDL evidence:** 3 results, ALL PASS
- **Pre/during/post evidence:** 3 results, ALL PASS
- **Source-range retry evidence:** 1 result, 2 retries, ALL PASS
- **Multi-row INSERT evidence:** 2 results, ALL PASS
- **Strict post-DDL evidence:** 3 results, 0 overlaps, ALL PASS
- **Expected INSTANT reject evidence:** 1 result, ALL PASS
