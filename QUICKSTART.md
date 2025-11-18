# Orchestro CLI Quick Start 🚀

## 5-Minute Tutorial

### Step 1: Install

```bash
cd standalone-orchestro
pip install -e .
```

### Step 2: Create a Test Scenario

Create `test.yaml`:

```yaml
name: My First Test
command: ls
timeout: 10

steps:
  - note: "Running ls command..."

validations:
  - type: path_exists
    path: test.yaml
    description: "Test file exists"
```

### Step 3: Run It

```bash
orchestro test.yaml --verbose
```

You should see:
```
[CLI Orchestro] Spawning command: ls
[CLI Orchestro] Running ls command...
✅ Scenario completed successfully!
```

## Screenshot & Sentinel Example

For TUI apps with screenshot support:

### 1. Create Scenario

`screenshot_test.yaml`:
```yaml
name: Screenshot Test
command: ./my_tui_app
timeout: 30

steps:
  - screenshot: "startup"
    timeout: 10
    note: "Capturing startup state..."

  - screenshot: "after-5-seconds"
    timeout: 10

validations:
  - type: path_exists
    path: artifacts/screenshots/startup.svg
  - type: path_exists
    path: artifacts/screenshots/after-5-seconds.svg
```

### 2. Ensure Your App Supports Screenshots

Your Textual app needs:

```python
import os
import tempfile
from pathlib import Path

class MyApp(App):
    def on_mount(self):
        if os.getenv("VYB_AUTO_SCREENSHOT"):
            self.set_interval(0.5, self._check_screenshot_triggers)

    def _check_screenshot_triggers(self):
        # Cross-platform: uses system temp directory
        trigger_dir = Path(tempfile.gettempdir()) / ".vyb_orchestro" / "screenshot_triggers"
        if not trigger_dir.exists():
            return

        for trigger_file in trigger_dir.glob("*.trigger"):
            try:
                name = trigger_file.stem
                screenshot_dir = Path.cwd() / "artifacts" / "screenshots"
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                self.save_screenshot(
                    filename=f"{name}.svg",
                    path=str(screenshot_dir)
                )
                trigger_file.unlink()
            except:
                pass
```

### 3. Run Test

```bash
orchestro screenshot_test.yaml --verbose
```

Screenshots will appear in `artifacts/screenshots/`! Each screenshot or sentinel wait step logs telemetry (trigger timestamps, latency, success/failure) to `runlog.jsonl`, enabling automated guardrails. See [`docs/SCREENSHOT_SENTINEL_SPEC.md`](docs/SCREENSHOT_SENTINEL_SPEC.md) for the full workflow contract.

## Next Steps

- See `examples/` for more scenarios
- Read `README.md` for full documentation
- Check `docs/` for API reference

## Common Patterns

### Wait and Screenshot

```yaml
steps:
  - note: "Waiting for app to load..."
  - screenshot: "01-loaded"
    timeout: 10

  - send: "/help"
    note: "Showing help..."
  - screenshot: "02-help"
    timeout: 10
```

### File Validation

```yaml
validations:
  - type: path_exists
    path: output/results.csv

  - type: file_contains
    path: output/log.txt
    text: "Success.*completed"
```

### Interactive Session

```yaml
steps:
  - expect: "Ready>"
    timeout: 5

  - send: "process data.json"

  - expect: "Processing complete"
    timeout: 30
```

## Troubleshooting

**Problem**: Screenshots not created

**Solution**:
1. Check `VYB_AUTO_SCREENSHOT=1` is set (Orchestro does this automatically)
2. Verify app has screenshot monitoring code
3. Ensure app uses `tempfile.gettempdir()` for cross-platform compatibility

**Problem**: Validation fails

**Solution**:
1. Use `--verbose` to see what's happening
2. Check paths are correct (relative to working directory)
3. For screenshots, use `artifacts/screenshots/` prefix

**Problem**: Process hangs

**Solution**:
1. Increase timeout values
2. Remove `expect` patterns for TUI apps (they don't output to stdout)
3. Use time-based delays instead

## Get Help

- Full docs: `README.md`
- Examples: `examples/` directory
- Issues: Create an issue on GitHub
