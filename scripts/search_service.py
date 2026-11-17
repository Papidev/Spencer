"""Start Spencer's private search service without requiring account setup."""

import argparse
import os
import secrets
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("action", choices=("start", "stop"))
command = (
    ["up", "-d", "search"]
    if parser.parse_args().action == "start"
    else ["stop", "search"]
)

subprocess.run(
    ["docker", "compose", *command],
    cwd=Path(__file__).resolve().parents[1],
    env={
        **os.environ,
        "SPENCER_SEARCH_SECRET": os.environ.get("SPENCER_SEARCH_SECRET")
        or secrets.token_hex(32),
    },
    check=True,
)
