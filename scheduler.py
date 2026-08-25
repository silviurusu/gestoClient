r"""Ruleaza main.py dupa orarul din config_local.ini, ca serviciu Windows.

Inlocuieste task-urile programate din Windows Task Scheduler, mai putin watchdog-ul
(main.py --verify-last-run-finished): un watchdog pornit de acelasi proces pe care il
supravegheaza nu mai raporteaza nimic cand procesul cade, deci ramane supervizor extern.

Setare ca serviciu, cu nssm:
    nssm install GestoScheduler "<python.exe>" "<cale>\scheduler.py"
    nssm set GestoScheduler AppDirectory "<cale>"
    nssm start GestoScheduler
"""
import logging
import logging.handlers
import os
import subprocess
import sys
from configparser import ConfigParser

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

import util


CFG_FILE_NAME = "config_local.ini"
TIMEZONE = "Europe/Bucharest"

# jurnalul serviciului sta in afara folderului de trace, unde verify_last_run_finished
# citeste fiecare fisier ca pe o rulare main.py
LOG_FILE_NAME = "scheduler.log"
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 3


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        handlers=[
            logging.handlers.RotatingFileHandler(
                LOG_FILE_NAME,
                maxBytes=LOG_MAX_BYTES,
                backupCount=LOG_BACKUP_COUNT,
                encoding="utf8",
            ),
            logging.StreamHandler(),
        ],
    )


def run_job(name, python, working_dir, args):
    logging.info(f"{name}: pornit, main.py {' '.join(args)}")

    try:
        result = subprocess.run(
            [python, "main.py"] + args,
            cwd=working_dir,
            capture_output=True,
            text=True,
        )
        logging.info(f"{name}: cod {result.returncode} | {result.stdout.strip()}")
    except Exception:
        logging.exception(f"{name}: rularea a esuat")


def main():
    setup_logging()

    cfg = ConfigParser()
    cfg.read_file(open(CFG_FILE_NAME))

    python = cfg.get("scheduler", "python", fallback="") or sys.executable
    working_dir = cfg.get("scheduler", "working_dir", fallback="") or os.path.dirname(os.path.abspath(__file__))

    logging.info(f"python: {python}")
    logging.info(f"working_dir: {working_dir}")

    scheduler = BlockingScheduler(timezone=TIMEZONE)

    for job in util.parse_scheduler_jobs(cfg):
        scheduler.add_job(
            run_job,
            trigger=CronTrigger(timezone=TIMEZONE, **job["cron"]),
            args=(job["name"], python, working_dir, job["args"]),
            name=job["name"],
            # echivalentele IgnoreNew, respectiv StartWhenAvailable din Task Scheduler
            max_instances=1,
            misfire_grace_time=60,
        )

        logging.info(f"{job['name']}: {job['cron']} -> main.py {' '.join(job['args'])}")

    logging.info("Scheduler pornit.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler oprit.")


if __name__ == "__main__":
    main()
