# gestoClient

## Rulare ca serviciu Windows (scheduler.py)

`scheduler.py` (APScheduler) ruleaza `main.py` dupa un orar, ca serviciu Windows cu
[NSSM](https://nssm.cc/download). Inlocuieste task-urile programate, cu o exceptie: watchdog-ul
(`main.py --verify-last-run-finished`) ramane in Task Scheduler, ca supervizor extern.

Orarul sta **versionat**, un fisier per firma, langa XML-urile pe care le inlocuieste:
`task_schedule/<firma>/scheduler.ini`. `config_local.ini` nu e in git, deci un orar tinut acolo
s-ar pierde odata cu serverul; in `config_local.ini` raman doar caile si trimiterea catre orar.

`config_local.ini` pe server:

```ini
[scheduler]
python = C:\Users\Vectron\AppData\Local\Programs\Python\Python312\python.exe
working_dir = C:\Users\Vectron\gestoClientWME
schedule_file = task_schedule\andalusia\scheduler.ini
```

`task_schedule/andalusia/scheduler.ini`, versionat — fiecare `[scheduler:<nume>]` e un job:
argumentele date lui `main.py` plus orarul, in sintaxa cron APScheduler (`minute`, `hour`, `day`,
`month`, `day_of_week`).

Instalare:

1. `<python.exe> -m pip install apscheduler` — cu **acelasi** interpretor ca cel din
   `[scheduler] python`, altfel serviciul porneste dar lanseaza `main.py` cu alt Python.
2. Copiaza `nssm.exe` in folderul aplicatiei (e in `.gitignore`, nu se comite).
3. Contul care ruleaza serviciul are nevoie de dreptul **Log on as a service**:
   `secpol.msc` > Local Policies > User Rights Assignment > Log on as a service > adauga utilizatorul
   (sau `secedit /export /cfg secpol.txt`, editeaza `SeServiceLogonRight`, `secedit /configure /db secedit.sdb /cfg secpol.txt`;
   fisierele `secedit.*` / `secpol*.txt` rezultate sunt in `.gitignore`).
4. Instalare si pornire:
   ```
   nssm install GestoScheduler "<python.exe>" "<working_dir>\scheduler.py"
   nssm set GestoScheduler AppDirectory "<working_dir>"
   nssm set GestoScheduler ObjectName "<masina>\<utilizator>" "<parola>"
   nssm set GestoScheduler AppExit Default Restart
   nssm start GestoScheduler
   ```
   `ObjectName` nu e optional: fara el serviciul porneste ca LocalSystem, care are alta hiva HKCU
   si alt profil decat contul sub care e inregistrat COM-ul WinMentor si sub care e instalat Python.
   Acelasi cont ca task-urile din `task_schedule/`.
5. Dezactiveaza task-urile vechi din Task Scheduler, altfel importurile ruleaza de doua ori.

Serviciul isi scrie jurnalul in `scheduler.log`, cu rotatie — nu in folderul de trace, unde
`--verify-last-run-finished` citeste fiecare fisier ca pe o rulare `main.py`. `config_local.ini`
trebuie sa aiba si `[winmentor] loginUser`, `loginPassword`, `[gesto] trace_folder`.

## Verificarea ca importul nu s-a blocat

`main.py --verify-last-run-finished=1` cauta cel mai recent log al unui run incheiat cu succes si, daca
nu gaseste unul mai nou de 20 de minute, trimite push ([ntfy.sh](https://ntfy.sh), canalul
`gesto-push-general`) si mail. Ruleaza din Task Scheduler, nu din `scheduler.py`, ca sa prinda si cazul
in care serviciul `GestoScheduler` a murit: `task_schedule/andalusia/WinMentor_verify_running.xml`,
la 15 minute intre 06:15 si 21:15 (decalat fata de import, ca sa verifice run-ul precedent).

Un run e considerat incheiat cu succes daca ultima linie din log e marcajul `TASK_FINISHED`. Log-urile de
maintenance (sufix `__maintenance`), cel in curs de scriere si cele in care `DocImpServer.exe` rula deja
sunt ignorate.

**La prima instalare**, porneste `main.py` o data si asigura-te ca a scris marcajul, inainte sa activezi
task-ul de verificare - log-urile mai vechi nu contin marcajul si ar declansa o alarma falsa.

## Generarea wrapper-ului COM (gen_py) din tlb

`winmentor.py` incarca direct `tlb/WMDocImpServer.tlb` prin `pythoncom.LoadTypeLib`, deci in mod normal
nu e nevoie de nimic. Wrapper-ul generat (`gen_py`) e util doar cand vrei sa vezi semnaturile metodelor
expuse de DocImpServer:

```
python -m win32com.client.makepy tlb/WMDocImpServer.tlb
```

Rezultatul ajunge in `site-packages/win32com/gen_py`.
