@echo off
rem @echo on
SETLOCAL ENABLEDELAYEDEXPANSION

set args=

FOR %%A IN (%*) DO (
    rem echo %%A
    FOR /f "tokens=1,2 delims=:" %%G IN ("%%A") DO (
        rem echo %%G - %%H
        set args=!args! --%%G=%%H
        rem echo !args!
    )
)

rem echo %args%

echo c:\Python27\python.exe main.py --generateIntrariDinProductie=1 --generateWorkOrders=1 --exportSummaryTransfers=1 --generateMonetare=1 %args%
c:\Python27\python.exe main.py --generateIntrariDinProductie=1 --generateWorkOrders=1 --exportSummaryTransfers=1 --generateMonetare=1 %args%

rem echo c:\Python27\python.exe main.py --generateIntrariDinProductie=1 --generateWorkOrders=1 --exportSummaryTransfers=1 %args%
rem c:\Python27\python.exe main.py --generateIntrariDinProductie=1 --generateWorkOrders=1 --exportSummaryTransfers=1 %args%

rem echo c:\Python27\python.exe main.py --generateIntrariDinProductie=1 --generateWorkOrders=1 %args%
rem c:\Python27\python.exe main.py --generateIntrariDinProductie=1 --generateWorkOrders=1 %args%

rem echo c:\Python27\python.exe main.py --exportSummaryTransfers=1 --generateMonetare=1 %args%
rem c:\Python27\python.exe main.py --exportSummaryTransfers=1 --generateMonetare=1 %args%

rem echo c:\Python27\python.exe main.py --generateMonetare=1 %args%
rem c:\Python27\python.exe main.py --generateMonetare=1 %args%

rem echo c:\Python27\python.exe main.py --exportSummaryTransfers=1 %args%
rem c:\Python27\python.exe main.py --exportSummaryTransfers=1 %args%
