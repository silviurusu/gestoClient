# gestoClient

## Rulare ca serviciu Windows (scheduler.py)

`scheduler.py` (APScheduler) inlocuieste task-urile din Task Scheduler: ruleaza `main.py` la 15 minute
intre 06:00 si 21:00 si `remove_old_files.py` zilnic. Se instaleaza ca serviciu cu [NSSM](https://nssm.cc/download).

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

## Generarea wrapper-ului COM (gen_py) din tlb

`winmentor.py` incarca direct `tlb/WMDocImpServer.tlb` prin `pythoncom.LoadTypeLib`, deci in mod normal
nu e nevoie de nimic. Wrapper-ul generat (`gen_py`) e util doar cand vrei sa vezi semnaturile metodelor
expuse de DocImpServer:

```
python -m win32com.client.makepy tlb/WMDocImpServer.tlb
```

Rezultatul ajunge in `site-packages/win32com/gen_py`.
