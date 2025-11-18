"""Snapshot storage management in git-friendly format.

Stores snapshots in a structured directory layout:
    .snapshots/
    ├── scenario_slug/
    │   ├── stdout.txt
    │   ├── stderr.txt
    │   └── metadata.json

This format ensures:
- Clean git diffs
- Human-readable snapshots
- Easy manual inspection
- Efficient storage
"""

import hashlib
import json
from pathlib import Path
from typing import Optional

from .models import Snapshot, CapturedOutput


class SnapshotStorage:
    """Manages snapshot storage and retrieval.

    Single Responsibility: Handle snapshot persistence in git-friendly format.
    """

    def __init__(self, snapshot_dir: Path = Path(".snapshots")):
        """Initialize snapshot storage.

        Args:
            snapshot_dir: Base directory for snapshots (default: .snapshots)
        """
        self.snapshot_dir = snapshot_dir.resolve()

    def save(self, snapshot: Snapshot) -> None:
        """Save snapshot to disk in git-friendly format.

        Creates directory structure:
            .snapshots/{scenario_slug}/
            ├── stdout.txt
            ├── stderr.txt
            └── metadata.json

        Args:
            snapshot: Snapshot to save
        """
        snapshot_path = self._get_snapshot_path(snapshot.scenario_name)
        snapshot_path.mkdir(parents=True, exist_ok=True)

        # Save stdout
        stdout_file = snapshot_path / "stdout.txt"
        self._write_text(stdout_file, snapshot.output.stdout)

        # Save stderr
        stderr_file = snapshot_path / "stderr.txt"
        self._write_text(stderr_file, snapshot.output.stderr)

        # Calculate checksum
        checksum = self._calculate_checksum(snapshot.output)

        # Save metadata
        metadata = {
            "scenario_name": snapshot.scenario_name,
            "exit_code": snapshot.output.exit_code,
            "timestamp": snapshot.output.timestamp.isoformat(),
            "created_at": snapshot.created_at.isoformat(),
            "updated_at": snapshot.updated_at.isoformat(),
            "checksum": checksum,
            "metadata": snapshot.output.metadata,
        }

        metadata_file = snapshot_path / "metadata.json"
        self._write_json(metadata_file, metadata)

    def load(self, scenario_name: str) -> Optional[Snapshot]:
        """Load snapshot from disk.

        Args:
            scenario_name: Name of scenario to load

        Returns:
            Snapshot if found, None otherwise
        """
        snapshot_path = self._get_snapshot_path(scenario_name)

        if not snapshot_path.exists():
            return None

        # Load files
        stdout_file = snapshot_path / "stdout.txt"
        stderr_file = snapshot_path / "stderr.txt"
        metadata_file = snapshot_path / "metadata.json"

        # Check all required files exist
        if not all(
            f.exists() for f in [stdout_file, stderr_file, metadata_file]
        ):
            return None

        # Read files
        stdout = self._read_text(stdout_file)
        stderr = self._read_text(stderr_file)
        metadata = self._read_json(metadata_file)

        # Create snapshot
        from datetime import datetime

        output = CapturedOutput(
            stdout=stdout,
            stderr=stderr,
            exit_code=metadata["exit_code"],
            timestamp=datetime.fromisoformat(metadata["timestamp"]),
            metadata=metadata.get("metadata", {}),
        )

        snapshot = Snapshot(
            scenario_name=metadata["scenario_name"],
            output=output,
            created_at=datetime.fromisoformat(metadata["created_at"]),
            updated_at=datetime.fromisoformat(metadata["updated_at"]),
            checksum=metadata.get("checksum"),
        )

        # Verify checksum
        expected_checksum = self._calculate_checksum(output)
        if snapshot.checksum and snapshot.checksum != expected_checksum:
            raise ValueError(
                f"Checksum mismatch for {scenario_name}: "
                f"expected {snapshot.checksum}, got {expected_checksum}"
            )

        return snapshot

    def exists(self, scenario_name: str) -> bool:
        """Check if snapshot exists.

        Args:
            scenario_name: Name of scenario

        Returns:
            True if snapshot exists
        """
        snapshot_path = self._get_snapshot_path(scenario_name)
        return (
            snapshot_path.exists()
            and (snapshot_path / "stdout.txt").exists()
            and (snapshot_path / "stderr.txt").exists()
            and (snapshot_path / "metadata.json").exists()
        )

    def delete(self, scenario_name: str) -> bool:
        """Delete snapshot.

        Args:
            scenario_name: Name of scenario

        Returns:
            True if deleted, False if didn't exist
        """
        snapshot_path = self._get_snapshot_path(scenario_name)

        if not snapshot_path.exists():
            return False

        # Remove all files in snapshot directory
        for file in snapshot_path.iterdir():
            file.unlink()

        # Remove directory
        snapshot_path.rmdir()

        return True

    def list_scenarios(self) -> list[str]:
        """List all stored scenarios.

        Returns:
            List of scenario names
        """
        if not self.snapshot_dir.exists():
            return []

        scenarios = []
        for path in self.snapshot_dir.iterdir():
            if path.is_dir() and (path / "metadata.json").exists():
                metadata = self._read_json(path / "metadata.json")
                scenarios.append(metadata["scenario_name"])

        return sorted(scenarios)

    def get_snapshot_path(self, scenario_name: str) -> Path:
        """Get path to snapshot directory (public API).

        Args:
            scenario_name: Name of scenario

        Returns:
            Path to snapshot directory
        """
        return self._get_snapshot_path(scenario_name)

    def _get_snapshot_path(self, scenario_name: str) -> Path:
        """Get path to snapshot directory for scenario.

        Args:
            scenario_name: Name of scenario

        Returns:
            Path to snapshot directory
        """
        # Create slug from scenario name
        import re

        slug = scenario_name.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)

        return self.snapshot_dir / slug

    def _calculate_checksum(self, output: CapturedOutput) -> str:
        """Calculate SHA256 checksum of output.

        Args:
            output: Captured output

        Returns:
            Hex digest of checksum
        """
        hasher = hashlib.sha256()
        hasher.update(output.stdout.encode("utf-8"))
        hasher.update(output.stderr.encode("utf-8"))
        hasher.update(str(output.exit_code).encode("utf-8"))
        return hasher.hexdigest()

    def _write_text(self, path: Path, content: str) -> None:
        """Write text file with UTF-8 encoding.

        Args:
            path: File path
            content: Text content
        """
        path.write_text(content, encoding="utf-8")

    def _read_text(self, path: Path) -> str:
        """Read text file with UTF-8 encoding.

        Args:
            path: File path

        Returns:
            Text content
        """
        return path.read_text(encoding="utf-8")

    def _write_json(self, path: Path, data: dict) -> None:
        """Write JSON file with pretty formatting.

        Args:
            path: File path
            data: Dictionary to write
        """
        path.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def _read_json(self, path: Path) -> dict:
        """Read JSON file.

        Args:
            path: File path

        Returns:
            Parsed JSON data
        """
        return json.loads(path.read_text(encoding="utf-8"))
