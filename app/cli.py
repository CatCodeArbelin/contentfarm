from __future__ import annotations

import argparse
import json

from app.collectors.runner import collect_active_sources
from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(prog="contentfarm")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("collect", help="Run collectors for all active sources")
    args = parser.parse_args()

    if args.command == "collect":
        with SessionLocal() as db:
            print(json.dumps(collect_active_sources(db), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
