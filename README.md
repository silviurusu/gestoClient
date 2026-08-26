# gestoClient

## Scheduler

`scheduler.py` ruleaza `main.py` dupa un orar, ca serviciu Windows. Inlocuieste task-urile
programate, cu o exceptie: watchdog-ul (`main.py --verify-last-run-finished`) ramane in
Windows Task Scheduler, ca supervizor extern — un watchdog pornit de procesul pe care il
supravegheaza nu mai raporteaza nimic cand acel proces cade.

Orarul sta **versionat**, un fisier per firma, langa XML-urile pe care le inlocuieste:
`task_schedule/<firma>/scheduler.ini`. `config_local.ini` nu e in git, deci un orar tinut
acolo s-ar pierde odata cu serverul; in `config_local.ini` raman doar caile si trimiterea
catre orarul folosit.

`config_local.ini` pe server:

```ini
[scheduler]
python = C:\Users\vectron\AppData\Local\Programs\Python\Python312\python.exe
working_dir = c:\Vectron\gestoClient
schedule_file = task_schedule\Carmic\scheduler.ini
```

`task_schedule/Carmic/scheduler.ini`, versionat — fiecare `[scheduler:<nume>]` e un job:
argumentele date lui `main.py` plus orarul, in sintaxa cron APScheduler (`minute`, `hour`,
`day`, `month`, `day_of_week`):

```ini
[scheduler:export]
args = --exportWinMentorData=1
hour = 6-22
minute = */5

[scheduler:trace_files]
args = --delete-old-trace-files=1 --days-ago=20
hour = 8
minute = 43
```

Campurile mai fine decat cel mai putin semnificativ camp precizat iau valoarea minima:
`hour = 8` fara `minute` inseamna 8:00 fix. O cheie care nu e camp cron opreste pornirea
serviciului, in loc sa fie ignorata tacut de APScheduler.

Setarile serviciului, per firma, sunt in `task_schedule/<firma>/nssm.txt`.

Instalare:

```
<python.exe> -m pip install apscheduler

nssm install GestoScheduler "<python.exe>" "<working_dir>\scheduler.py"
nssm set GestoScheduler AppDirectory "<working_dir>"
nssm set GestoScheduler ObjectName "<masina>\<utilizator>" "<parola>"
nssm set GestoScheduler AppExit Default Restart
nssm start GestoScheduler
```

`ObjectName` nu e optional: fara el serviciul porneste ca LocalSystem, care are alta
hiva HKCU si alt profil decat contul sub care e inregistrat COM-ul WinMentor si sub care
e instalat Python. Acelasi cont ca task-urile din task_schedule/.

`pip install` se face cu **acelasi** interpretor ca cel din `[scheduler] python`, altfel
scheduler-ul porneste dar lanseaza main.py cu alt Python.

Serviciul isi scrie jurnalul in `scheduler.log`, cu rotatie — nu in folderul de trace,
unde `--verify-last-run-finished` citeste fiecare fisier ca pe o rulare `main.py`.

## Teste

```
pytest
```
