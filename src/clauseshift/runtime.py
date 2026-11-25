"""Runtime helpers: thread count and an honest description of the hardware a run used."""

from __future__ import annotations

import os
import platform


def num_threads() -> int:
    """Threads for torch: $CLAUSESHIFT_THREADS if set, else the number of CPUs available to this process."""
    if os.environ.get("CLAUSESHIFT_THREADS"):
        return int(os.environ["CLAUSESHIFT_THREADS"])
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:
        return os.cpu_count() or 1


def cpu_model() -> str:
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def hardware_string(threads: int) -> str:
    """Detected at run time, so the metadata never claims hardware the run did not use."""
    import torch

    if torch.cuda.is_available():
        return f"GPU, {torch.cuda.get_device_name(0)}"
    return f"CPU, {cpu_model()}, {threads} threads"
