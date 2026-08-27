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


# caile se rezolva fata de scriptul insusi: un serviciu porneste implicit in
# C:\Windows\System32, iar nssm ajunge in folderul aplicatiei doar daca i s-a dat AppDirectory
APP_DIR = os.path.dirname(os.path.abspath(__file__))

CFG_FILE_NAME = os.path.join(APP_DIR, "config_local.ini")
TIMEZONE = "Europe/Bucharest"

# jurnalul serviciului sta in afara folderului de trace, unde verify_last_run_finished
# citeste fiecare fisier ca pe o rulare main.py
LOG_FILE_NAME = os.path.join(APP_DIR, "scheduler.log")
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 3

# cat ii mai dam unei rulari sa se stinga dupa taskkill, inainte sa renuntam la ea
KILL_GRACE = 30


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


def kill_job_tree(name, pid):
    """Opreste rularea cu tot cu procesele pornite de ea: /T coboara in tot arborele.

    DocImpServer.exe nu e printre ele - fiind server COM, il porneste svchost, nu main.py -
    dar de orfanii lui se ocupa killOrphanDocImpServers la rularea urmatoare."""
    killed = subprocess.run(
        ["taskkill", "/PID", str(pid), "/T", "/F"],
        capture_output=True,
        text=True,
    )

    # taskkill scrie cate un rand per proces oprit, iar jurnalul se citeste pe linii
    output = " ".join((killed.stdout.strip() or killed.stderr.strip()).split())
    logging.info(f"{name}: taskkill {pid} -> cod {killed.returncode} | {output}")


def run_job(name, python, working_dir, args, timeout):
    logging.info(f"{name}: pornit, main.py {' '.join(args)}")

    try:
        job = subprocess.Popen(
            [python, "main.py"] + args,
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            stdout, _ = job.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            # fara asta o rulare intepenita opreste jobul definitiv: cu max_instances=1
            # urmatoarele nici nu mai pornesc, deci exportul tace pana observa cineva
            logging.warning(f"{name}: n-a terminat in {timeout} s, il opresc")
            kill_job_tree(name, job.pid)

            try:
                stdout, _ = job.communicate(timeout=KILL_GRACE)
            except subprocess.TimeoutExpired:
                logging.error(f"{name}: nu s-a inchis nici dupa taskkill")
                return

            logging.warning(f"{name}: oprit dupa {timeout} s | {stdout.strip()}")

            return

        logging.info(f"{name}: cod {job.returncode} | {stdout.strip()}")
    except Exception:
        logging.exception(f"{name}: rularea a esuat")


def main():
    setup_logging()

    cfg = ConfigParser()
    cfg.read_file(open(CFG_FILE_NAME))

    python = cfg.get("scheduler", "python", fallback="") or sys.executable
    working_dir = cfg.get("scheduler", "working_dir", fallback="") or APP_DIR

    logging.info(f"python: {python}")
    logging.info(f"working_dir: {working_dir}")

    schedule_path = util.scheduler_schedule_path(cfg, APP_DIR)
    logging.info(f"orar: {schedule_path}")

    schedule = ConfigParser()
    schedule.read_file(open(schedule_path))

    scheduler = BlockingScheduler(timezone=TIMEZONE)

    for job in util.parse_scheduler_jobs(schedule):
        scheduler.add_job(
            run_job,
            trigger=CronTrigger(timezone=TIMEZONE, **job["cron"]),
            args=(job["name"], python, working_dir, job["args"], job["timeout"]),
            name=job["name"],
            # echivalentele IgnoreNew, respectiv StartWhenAvailable din Task Scheduler
            max_instances=1,
            misfire_grace_time=60,
        )

        logging.info(
            f"{job['name']}: {job['cron']} -> main.py {' '.join(job['args'])}"
            f" (timeout {job['timeout']} s)"
        )

    logging.info("Scheduler pornit.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler oprit.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # sub nssm, stderr nu ajunge nicaieri daca nu i s-a dat AppStderr: o eroare de config
        # ar produce o bucla de repornire muta, cu jurnalul oprit dupa antet
        logging.exception("Eroare la pornirea scheduler-ului")
        raise
