from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.combining import AndTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import subprocess
import logging
from datetime import datetime

# pentru setare ca serviciu
# nssm install GestoScheduler "C:\Users\Vectron\AppData\Local\Programs\Python\Python312\python.exe" "C:\Users\Vectron\gestoClientWME\scheduler.py"
# nssm set GestoScheduler AppDirectory "C:\Users\Vectron\gestoClientWME"
# nssm start GestoScheduler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('debug/scheduler.log'),
        logging.StreamHandler()
    ]
)

def run_gesto():
    now = datetime.now()    
    
    logging.info("Starting importa documente din gesto...")

    try:
        args = [
                    r"C:\Users\Vectron\AppData\Local\Programs\Python\Python312\python.exe",
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
            cwd=r"C:\Users\Vectron\gestoClientWME",
            capture_output=True,
            text=True
        )
        logging.info(f"Completed in {result.returncode} | Output: {result.stdout.strip()}")
    except Exception as e:
        logging.error(f"Failed: {e}")    


def sterge_fisiere_vechi():
    now = datetime.now()    
    
    logging.info("Starting sterge fisiere vechi...")
    try:
        result = subprocess.run(
            [
                r"C:\Users\Vectron\AppData\Local\Programs\Python\Python312\python.exe",
                "remove_old_files.py"                
            ],
            cwd=r"C:\Users\Vectron\gestoClientWME",
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