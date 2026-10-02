# cli.py
from __future__ import annotations

import argparse
import subprocess
import sys

import structlog

from scheduler.jobs import run_pipeline, schedule_jobs

logger = structlog.get_logger(__name__)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Hali Pipeline – Automated ETL for Kenyan Public Data"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Run a pipeline once
    run_parser = subparsers.add_parser("run", help="Execute a pipeline once")
    run_parser.add_argument(
        "--pipeline",
        choices=["weather", "nse", "cbk", "all"],
        required=True,
        help="Target pipeline to execute",
    )

    # Start the scheduler daemon
    subparsers.add_parser("schedule", help="Start the APScheduler daemon")

    # Launch Streamlit dashboard
    subparsers.add_parser("dashboard", help="Launch the Streamlit analytics dashboard")

    args = parser.parse_args(argv)

    if args.command == "run":
        pipelines = ["weather", "nse", "cbk"] if args.pipeline == "all" else [args.pipeline]
        for p in pipelines:
            logger.info("CLI running pipeline", pipeline=p)
            run_pipeline(p)

    elif args.command == "schedule":
        logger.info("CLI starting scheduler")
        schedule_jobs()

    elif args.command == "dashboard":
        logger.info("CLI launching Streamlit dashboard")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard/app.py"], check=True)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

