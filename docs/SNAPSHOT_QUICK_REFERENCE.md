# Snapshot Testing - Quick Reference

## Command Cheat Sheet

```bash
# Record new snapshots
orchestro run scenario.yaml --snapshot=record

# Verify snapshots (CI/CD)
orchestro run scenario.yaml --snapshot=verify

# Update snapshots
orchestro run scenario.yaml --snapshot=update

# Update with confirmation
orchestro run scenario.yaml --snapshot=update --snapshot-update-confirm

# Custom snapshot directory
orchestro run scenario.yaml --snapshot=verify --snapshot-dir=test/snapshots

# With JUnit XML report
orchestro run scenario.yaml --snapshot=verify --junit-xml=results.xml
```

## Directory Structure

```
.snapshots/
└── scenario-name/
    ├── stdout.txt      # Standard output
    ├── stderr.txt      # Standard error
    └── metadata.json   # Exit code, timestamps, checksum
```

## Modes

| Mode | Purpose | Use Case | Behavior if Exists |
|------|---------|----------|-------------------|
| `record` | Create new snapshots | Initial baseline | **Fails** |
| `verify` | Check outputs match | CI/CD pipelines | Compares |
| `update` | Modify snapshots | After code changes | Overwrites |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Snapshots match (verify) or created/updated successfully |
| 1 | Snapshot mismatch (verify) or creation failed |

## Diff Output

```
Snapshot Comparison
======================================================================

✗ Outputs differ (87.5% similarity)

STDOUT Differences:
----------------------------------------------------------------------
@@ -1,3 +1,3 @@
  Hello, World!
- Version: 1.0.0
+ Version: 2.0.0
  Ready!
```

## Similarity Scoring

| Score | Meaning |
|-------|---------|
| 100% | Perfect match |
| 90-99% | Nearly identical |
| 70-89% | Some differences |
| < 70% | Significant changes |

**Weighted calculation:**
- Stdout: 60%
- Stderr: 30%
- Exit code: 10%

## Common Workflows

### Initial Setup

```bash
# 1. Create scenario.yaml
# 2. Record baseline
orchestro run scenario.yaml --snapshot=record

# 3. Commit snapshot
git add .snapshots/scenario-name/
git commit -m "Add baseline snapshot for scenario"
```

### CI/CD Pipeline

```bash
# In .github/workflows/test.yml or .gitlab-ci.yml
orchestro run scenario.yaml --snapshot=verify --junit-xml=results.xml
```

### After Code Changes

```bash
# 1. Run tests (will fail if output changed)
orchestro run scenario.yaml --snapshot=verify

# 2. Review changes
git diff .snapshots/

# 3. If intentional, update snapshots
orchestro run scenario.yaml --snapshot=update --snapshot-update-confirm

# 4. Commit updated snapshots
git add .snapshots/
git commit -m "Update snapshots for new output format"
```

## Python API

```python
from orchestro_cli.snapshot import SnapshotEngine, SnapshotMode
from pathlib import Path

# Record
engine = SnapshotEngine(mode=SnapshotMode.RECORD)
result = engine.record_snapshot(
    scenario_name="My Test",
    stdout="Hello, World!\n",
    stderr="",
    exit_code=0
)

# Verify
engine = SnapshotEngine(mode=SnapshotMode.VERIFY)
result = engine.verify_snapshot(
    scenario_name="My Test",
    stdout="Hello, World!\n",
    stderr="",
    exit_code=0
)

if result.passed:
    print("✓ Snapshot matches")
else:
    print(f"✗ Mismatch: {result.message}")
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Checksum mismatch | Re-record snapshot |
| Flaky snapshots | Normalize timestamps/UUIDs in output |
| Large diffs slow | Reduce context lines or split scenarios |
| Git conflicts | Resolve like regular text files |
| Snapshot not found | Record it first with `--snapshot=record` |

## Best Practices

✓ **DO:**
- Commit snapshots with code changes
- Review snapshot diffs in PRs
- Use descriptive scenario names
- Keep scenarios focused and small
- Update snapshots when output intentionally changes

✗ **DON'T:**
- Ignore snapshot failures in CI
- Update snapshots blindly
- Create snapshots for non-deterministic output
- Store large binaries in snapshots
- Manually edit snapshot files

## File Locations

| Path | Description |
|------|-------------|
| `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/orchestro_cli/snapshot/` | Implementation |
| `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/tests/snapshot/` | Tests |
| `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/docs/SNAPSHOT_TESTING.md` | Full documentation |

## Quick Tips

💡 **Tip 1:** Use `--snapshot-update-confirm` during development to review each update

💡 **Tip 2:** Set `SNAPSHOT_UPDATE=1` env var to auto-update in dev (custom implementation)

💡 **Tip 3:** Use `git diff --word-diff .snapshots/` for readable snapshot diffs

💡 **Tip 4:** Add `.snapshots/` to `.gitattributes` with `*.txt diff=default` for better diffs

💡 **Tip 5:** Snapshot failures show full diffs - read them carefully before updating!

## Integration Examples

### GitHub Actions

```yaml
- name: Run tests with snapshots
  run: |
    orchestro run scenario.yaml --snapshot=verify --junit-xml=results.xml
```

### GitLab CI

```yaml
test:
  script:
    - orchestro run scenario.yaml --snapshot=verify --junit-xml=results.xml
  artifacts:
    reports:
      junit: results.xml
```

### Jenkins

```groovy
sh 'orchestro run scenario.yaml --snapshot=verify --junit-xml=results.xml'
junit 'results.xml'
```

## Performance

| Output Size | Typical Time |
|-------------|--------------|
| < 1KB | < 10ms |
| 1-100KB | 10-50ms |
| 100KB-1MB | 50-200ms |
| > 1MB | 200ms-1s |

---

**For complete documentation, see:** `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/docs/SNAPSHOT_TESTING.md`
