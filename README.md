# gestoClient

## Scheduler

`scheduler.py` ruleaza `main.py` dupa orarul din `config_local.ini`, ca serviciu Windows.
Inlocuieste task-urile programate, cu o exceptie: watchdog-ul
(`main.py --verify-last-run-finished`) ramane in Windows Task Scheduler, ca supervizor
extern — un watchdog pornit de procesul pe care il supravegheaza nu mai raporteaza nimic
cand acel proces cade.

Orarul se scrie in `config_local.ini`, o sectiune per job (vezi `config.ini`):

```ini
[scheduler]
python = C:\Users\vectron\AppData\Local\Programs\Python\Python312\python.exe
working_dir = c:\Vectron\gestoClient

[scheduler:export]
args = --exportWinMentorData=1 --markedForWinMentorExport=1
hour = 6-21
minute = */5
```

Instalare:

```
pip install apscheduler

nssm install GestoScheduler "<python.exe>" "<working_dir>\scheduler.py"
nssm set GestoScheduler AppDirectory "<working_dir>"
nssm start GestoScheduler
```

Serviciul isi scrie jurnalul in `scheduler.log`, cu rotatie — nu in folderul de trace,
unde `--verify-last-run-finished` citeste fiecare fisier ca pe o rulare `main.py`.

## Teste

```
pytest
```
