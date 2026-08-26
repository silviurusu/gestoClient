# gestoClient

## Rulare ca serviciu Windows (scheduler.py)

`scheduler.py` (APScheduler) inlocuieste task-urile din Task Scheduler: ruleaza `main.py` la 15 minute
intre 06:00 si 21:00 si `main.py --delete-old-trace-files=1` zilnic. Se instaleaza ca serviciu cu
[NSSM](https://nssm.cc/download). Interpretorul si folderul aplicatiei sunt cele cu care porneste
scheduler-ul, deci nu trebuie editate cai in cod.

1. `pip install apscheduler`
2. Copiaza `nssm.exe` in folderul aplicatiei (e in `.gitignore`, nu se comite).
3. Contul care ruleaza serviciul are nevoie de dreptul **Log on as a service**:
   `secpol.msc` > Local Policies > User Rights Assignment > Log on as a service > adauga utilizatorul
   (sau `secedit /export /cfg secpol.txt`, editeaza `SeServiceLogonRight`, `secedit /configure /db secedit.sdb /cfg secpol.txt`;
   fisierele `secedit.*` / `secpol*.txt` rezultate sunt in `.gitignore`).
4. Instalare si pornire (caile sunt cele de la Andalusia, adapteaza-le):
   ```
   nssm install GestoScheduler "C:\Users\Vectron\AppData\Local\Programs\Python\Python312\python.exe" "C:\Users\Vectron\gestoClientWME\scheduler.py"
   nssm set GestoScheduler AppDirectory "C:\Users\Vectron\gestoClientWME"
   nssm start GestoScheduler
   ```
5. Dezactiveaza task-urile vechi din Task Scheduler (`task_schedule/<client>/*.xml`), altfel importurile ruleaza de doua ori.

Log-ul serviciului: `debug/scheduler.log`. `config_local.ini` trebuie sa aiba `[winmentor] loginUser`, `loginPassword` si `[gesto] trace_folder`.

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
