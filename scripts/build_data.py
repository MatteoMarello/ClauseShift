"""Generate ClauseShift, run integrity checks, write data/*.jsonl and data/manifest.json."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from clauseshift.data import build, check, write  # noqa: E402

config = json.loads(Path("configs/data.json").read_text())
splits = build(config)
stats = check(splits)
manifest = write(splits, stats, config, Path("data"))
print(json.dumps(stats, indent=1))
print({k: v["sha256_content"][:16] for k, v in manifest["files"].items()})
