from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Union


async def run_tf_init_command(directory: Union[str, Path]) -> str:
    proc = await asyncio.create_subprocess_exec(
        "terraform",
        "init",
        "-input=false",
        cwd=str(directory),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    if proc.returncode:
        raise RuntimeError(
            f"Error running terraform init -input=false : {stdout.decode().strip()}"
        )
    return stdout.decode()
