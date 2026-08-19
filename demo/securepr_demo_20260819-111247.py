import subprocess
from collections.abc import Sequence


def run_command(parts: Sequence[str]) -> int:
    print("debug: running command")
    completed = subprocess.run(list(parts), shell=True, check=False)
    return completed.returncode