import logging
import subprocess

from backend.config import settings


logger = logging.getLogger(__name__)


def run_command(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    if settings.dry_run_system:
        logger.info("DRY_RUN: %s", " ".join(command))
        return subprocess.CompletedProcess(command, 0, "", "")
    return subprocess.run(command, check=check, text=True, capture_output=True)

