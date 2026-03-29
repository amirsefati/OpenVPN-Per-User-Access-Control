import logging
import os
import subprocess
from pathlib import Path

from backend.config import settings


logger = logging.getLogger(__name__)


def run_command(
    command: list[str],
    check: bool = True,
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    if settings.dry_run_system:
        logger.info("DRY_RUN: %s", " ".join(command))
        return subprocess.CompletedProcess(command, 0, "", "")

    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    result = subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=True,
        cwd=str(cwd) if cwd else None,
        env=merged_env,
    )
    if result.returncode != 0:
        logger.error("Command failed: %s", " ".join(command))
        if cwd:
            logger.error("cwd: %s", cwd)
        if result.stdout:
            logger.error("stdout: %s", result.stdout.strip())
        if result.stderr:
            logger.error("stderr: %s", result.stderr.strip())
        if check:
            raise subprocess.CalledProcessError(
                result.returncode,
                command,
                output=result.stdout,
                stderr=result.stderr,
            )
    return result
