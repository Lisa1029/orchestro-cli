# Snapshot Testing Guide

Orchestro's snapshot testing system enables regression testing via golden output comparison. Capture command outputs once, then automatically verify they stay consistent across changes.

## Quick Start

### Recording Snapshots

Record a baseline snapshot for your scenario:

```bash
orchestro run scenario.yaml --snapshot=record
```

This creates `.snapshots/scenario-name/` with:
- `stdout.txt` - Standard output
- `stderr.txt` - Standard error
- `metadata.json` - Exit code, timestamps, checksums

### Verifying Snapshots (CI/CD)

Verify outputs match recorded snapshots:

```bash
orchestro run scenario.yaml --snapshot=verify
```

Verification fails if outputs differ, perfect for CI/CD pipelines:
- Exit code ≠ 0 indicates failure
- Detailed diff shown in output
- JUnit XML includes snapshot results

### Updating Snapshots

After intentional changes, update snapshots:

```bash
orchestro run scenario.yaml --snapshot=update
```

With interactive confirmation:

```bash
orchestro run scenario.yaml --snapshot=update --snapshot-update-confirm
```

## Architecture

### Directory Structure

```
.snapshots/
├── hello-world/
│   ├── stdout.txt         # Plain text output
│   ├── stderr.txt         # Plain text errors
│   └── metadata.json      # Exit code, timestamps, checksum
├── complex-scenario/
│   ├── stdout.txt
│   ├── stderr.txt
│   └── metadata.json
└── test-with-errors/
    ├── stdout.txt
    ├── stderr.txt
    └── metadata.json
```

### Components

#### 1. Models (`orchestro_cli/snapshot/models.py`)
- **SnapshotMode**: VERIFY, UPDATE, RECORD
- **CapturedOutput**: Stores stdout, stderr, exit_code, metadata
- **Snapshot**: Immutable snapshot representation
- **DiffResult**: Comparison results with similarity scoring
- **SnapshotResult**: Verification outcome

#### 2. Storage (`orchestro_cli/snapshot/storage.py`)
- Git-friendly plain text format
- SHA256 checksums for integrity
- Handles unicode and large outputs
- Atomic save/load operations

#### 3. Differ (`orchestro_cli/snapshot/diff.py`)
- Git-style unified diffs
- Configurable context lines
- ANSI color support
- Similarity scoring (0-100%)

#### 4. Engine (`orchestro_cli/snapshot/engine.py`)
- Orchestrates record/verify/update
- Interactive confirmation mode
- Detailed error reporting

## CLI Flags

### `--snapshot=MODE`
- **verify**: Verify outputs match snapshots (CI/CD)
- **update**: Update existing snapshots or create new ones
- **record**: Record new snapshots (fails if exists)

### `--snapshot-dir=PATH`
Custom snapshot storage directory (default: `.snapshots`)

### `--snapshot-update-confirm`
Require interactive confirmation before updating snapshots

## Integration Examples

### GitHub Actions

```yaml
name: Test with Snapshots

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Orchestro
        run: pip install orchestro-cli

      - name: Verify snapshots
        run: orchestro run scenario.yaml --snapshot=verify --junit-xml=results.xml

      - name: Upload results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: results.xml
```

### GitLab CI

```yaml
test:
  image: python:3.11
  script:
    - pip install orchestro-cli
    - orchestro run scenario.yaml --snapshot=verify --junit-xml=results.xml
  artifacts:
    reports:
      junit: results.xml
```

### Update Workflow (Local Development)

```bash
# 1. Make code changes
git checkout -b feature/new-output-format

# 2. Update snapshots to reflect intentional changes
orchestro run scenario.yaml --snapshot=update --snapshot-update-confirm

# 3. Review changes
git diff .snapshots/

# 4. Commit updated snapshots
git add .snapshots/
git commit -m "Update snapshots for new output format"

# 5. Verify CI passes
git push origin feature/new-output-format
```

## Diff Output

When snapshots don't match, you get detailed diffs:

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

Exit Code Mismatch:
  Expected: 0
  Actual:   1
```

### Similarity Scoring

Weighted similarity calculation:
- **Stdout**: 60%
- **Stderr**: 30%
- **Exit code**: 10%

Perfect match: 100%
Complete mismatch: 0%

## Git Integration

### Tracking Snapshots

By default, snapshots are tracked in git for:
- Team collaboration
- Change visibility
- Easy review process

### Ignoring Snapshots

To ignore snapshots (not recommended for tests):

```gitignore
# .gitignore
.snapshots/
```

### Best Practices

1. **Commit snapshots with code changes** - Keep them in sync
2. **Review snapshot diffs** - Ensure changes are intentional
3. **Small, focused scenarios** - Easier to debug failures
4. **Normalize timestamps** - Strip timestamps from output if variable
5. **Use descriptive names** - Clear scenario names help debugging

## Advanced Usage

### Programmatic Usage

```python
from orchestro_cli.snapshot import SnapshotEngine, SnapshotMode
from pathlib import Path

# Record mode
engine = SnapshotEngine(
    mode=SnapshotMode.RECORD,
    snapshot_dir=Path(".snapshots"),
    verbose=True
)

result = engine.record_snapshot(
    scenario_name="My Test",
    stdout="Hello, World!\n",
    stderr="",
    exit_code=0,
    metadata={"command": "echo 'Hello, World!'"}
)

if result.passed:
    print(f"Snapshot recorded at: {result.snapshot_path}")
```

### Custom Storage Location

```python
from pathlib import Path

engine = SnapshotEngine(
    mode=SnapshotMode.VERIFY,
    snapshot_dir=Path("test/snapshots")
)
```

### JUnit Integration

Snapshot results are automatically included in JUnit XML reports:

```xml
<testcase name="scenario_name_snapshot" classname="orchestro.snapshot" time="1.234">
  <failure message="Snapshot mismatch for 'My Scenario'" type="SnapshotMismatchError">
Similarity: 87.5%

STDOUT Differences:
+ New line added
- Old line removed
  </failure>
</testcase>
```

## Testing

Run snapshot system tests:

```bash
# All snapshot tests
pytest tests/snapshot/ -v

# Specific components
pytest tests/snapshot/test_models.py
pytest tests/snapshot/test_storage.py
pytest tests/snapshot/test_diff.py
pytest tests/snapshot/test_engine.py

# With coverage
pytest tests/snapshot/ --cov=orchestro_cli.snapshot --cov-report=html
```

## Troubleshooting

### Checksum Mismatch

If you see "Checksum mismatch" errors:
1. Snapshot file was manually edited
2. File corruption occurred
3. Re-record the snapshot

### Large Output Performance

For very large outputs (>1MB):
- Consider splitting into smaller scenarios
- Use focused assertions instead
- Normalize output to reduce size

### Flaky Snapshots

If snapshots change unexpectedly:
- Strip timestamps from output
- Normalize environment-specific values
- Use controlled test environments
- Set fixed random seeds if applicable

## API Reference

### SnapshotMode

```python
class SnapshotMode(Enum):
    VERIFY = "verify"  # CI/CD mode
    UPDATE = "update"  # Update snapshots
    RECORD = "record"  # Record new only
```

### CapturedOutput

```python
@dataclass
class CapturedOutput:
    stdout: str
    stderr: str
    exit_code: int
    timestamp: datetime
    metadata: Dict[str, Any]
```

### SnapshotResult

```python
@dataclass
class SnapshotResult:
    passed: bool
    diff_result: Optional[DiffResult]
    message: str
    snapshot_exists: bool
    snapshot_path: Optional[str]
```

## Performance

### Benchmarks

- **Small output** (<1KB): <10ms per operation
- **Medium output** (1KB-100KB): 10-50ms
- **Large output** (100KB-1MB): 50-200ms
- **Very large** (>1MB): 200ms-1s

### Optimization Tips

1. **Parallel execution**: Multiple snapshots can be verified in parallel
2. **Checksum shortcuts**: Identical checksums skip full comparison
3. **Streaming diffs**: Large diffs don't load fully into memory
4. **Context lines**: Fewer context lines = faster diffs

## Migration Guide

### From Manual Verification

**Before:**
```yaml
validations:
  - type: file_contains
    path: output.txt
    text: "expected content"
```

**After:**
```bash
# Record once
orchestro run scenario.yaml --snapshot=record

# Verify automatically
orchestro run scenario.yaml --snapshot=verify
```

### From Other Tools

#### Jest/Vitest Snapshots

Orchestro snapshots are similar but:
- Plain text format (not serialized JS objects)
- Separate files for stdout/stderr
- Built-in checksum verification
- CLI-focused workflow

#### Pytest Snapshots (syrupy)

Key differences:
- Git-friendly directory structure
- Multiple output streams (stdout, stderr)
- Exit code tracking
- Interactive update mode

## Contributing

See `/home/jonbrookings/vibe_coding_projects/my-orchestro-copy/orchestro_cli/snapshot/` for implementation.

Key files:
- `models.py` - Domain models
- `storage.py` - Persistence layer
- `diff.py` - Comparison engine
- `engine.py` - Orchestration logic
- `junit_reporter.py` - JUnit integration

All PRs must:
- Add tests for new features
- Maintain >90% code coverage
- Include documentation updates
- Follow existing code patterns
