from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import os
import subprocess
import sys
import logging
from datetime import datetime

# instalarea ca serviciu Windows e descrisa in README.md

# interpretorul si folderul aplicatiei sunt cele cu care a pornit scheduler-ul,
# ca sa nu depinda de caile unui anume client
PYTHON = sys.executable
APP_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(APP_DIR, 'debug', 'scheduler.log')),
        logging.StreamHandler()
    ]
)

def run_gesto():
    now = datetime.now()    
    
    logging.info("Starting importa documente din gesto...")

    try:
        args = [
                    PYTHON,
                    "main.py",
                    "--markedForWinMentorExport=1",
                    "--exportWinMentorData=1"
                ]

        if now.minute == 0:
            args.append("--importAvize=1")
            args.append("--importFacturiIntrare=1")

        logging.info(f"Running with args: {' '.join(args[1:])}")

        result = subprocess.run(
            args,
            cwd=APP_DIR,
            capture_output=True,
            text=True
        )
        logging.info(f"Completed in {result.returncode} | Output: {result.stdout.strip()}")
    except Exception as e:
        logging.error(f"Failed: {e}")    


def sterge_fisiere_vechi():
    logging.info("Starting sterge fisiere vechi...")
    try:
        result = subprocess.run(
            [
                PYTHON,
                "main.py",
                "--delete-old-trace-files=1"
            ],
            cwd=APP_DIR,
            capture_output=True,
            text=True
        )
        logging.info(f"Completed in {result.returncode} | Output: {result.stdout.strip()}")
    except Exception as e:
        logging.error(f"Failed: {e}")

scheduler = BlockingScheduler(timezone="Europe/Bucharest")

# Runs every 15 minutes, daily from 06:00 to 21:00
scheduler.add_job(
    run_gesto,
    trigger=CronTrigger(
        hour="6-21",          # 6 AM to 8 PM (last run at 20:45)
        minute="*/15",        # every 15 minutes
        timezone="Europe/Bucharest"
    ),
    name="Importa/exporta documente din/catre Gesto",
    max_instances=1,          # equivalent to IgnoreNew
    misfire_grace_time=60     # equivalent to StartWhenAvailable
)

scheduler.add_job(
    sterge_fisiere_vechi,
    trigger=CronTrigger(
        hour="20",      
        minute="43",   
        timezone="Europe/Bucharest"
    ),
    name="Sterge fisiere vechi",
    max_instances=1,          # equivalent to IgnoreNew
    misfire_grace_time=60     # equivalent to StartWhenAvailable
)

logging.info("Scheduler started.")
logging.info("Press Ctrl+C to stop.")

try:
    scheduler.start()
except KeyboardInterrupt:
    logging.info("Scheduler stopped.")