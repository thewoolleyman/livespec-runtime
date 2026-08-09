"""Verify this repo's documented spec-governance default block."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Final

from returns.result import Success

from livespec_runtime.spec_governance import verify_livespec_jsonc_default_block

__all__: list[str] = []

_DRIFT_EXIT: Final = 2


def main() -> int:
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    logger = logging.getLogger("check_spec_governance_default_block")
    result = verify_livespec_jsonc_default_block(path=Path(".livespec.jsonc"))
    if isinstance(result, Success):
        logger.info(json.dumps(result.unwrap(), sort_keys=True))
        return 0
    logger.error(result.failure())
    return _DRIFT_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
