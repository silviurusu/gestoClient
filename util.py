import datetime
import settings
import logging
import functools
import re
import inspect
from configparser import ConfigParser
import html
from django.template import loader
from django.utils.html import strip_tags
import traceback
import json
from decimal import Decimal
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import decorators
import os


logger = logging.getLogger(__name__)


# folderul aplicatiei e cel in care sta util.py: caile din config_local.ini sunt relative
# la el, nu la directorul din care s-a pornit rularea
APP_DIR = os.path.dirname(os.path.abspath(__file__))


# Reteaua de la client are pene scurte de DNS: un getaddrinfo poate expira o data
# si reusi la reincercarea urmatoare. Reincercam doar esecurile de connect, care
# se produc inainte ca requestul sa plece de pe masina, deci raman idempotente
# inclusiv pentru POST. Erorile de read (read=0) nu se reincearca.
CONNECT_RETRIES = 3
CONNECT_BACKOFF = 1.5

SESSION = requests.Session()
_retrying_adapter = HTTPAdapter(max_retries=Retry(
    total=None,
    connect=CONNECT_RETRIES,
    read=0,
    status=0,
    backoff_factor=CONNECT_BACKOFF,
))
SESSION.mount("https://", _retrying_adapter)
SESSION.mount("http://", _retrying_adapter)


def setup_logging(
        default_path='logging.json',
        default_level=logging.INFO,
        env_key='LOG_CFG',
        log_details=None
        ):
    """ Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)

            # Search for hadlers with "folder" and set the
            # .. log file with current date in that folder
            for _, dhandler in config["handlers"].items():
                folder = dhandler.pop("folder", None)
                if folder:
                    path = os.path.join(
                            folder,
                            datetime.datetime.strftime(datetime.datetime.now(), f"%Y_%m_%d__%H_%M") + (f"__{log_details}" if log_details is not None else "") + ".log"
                            )

                    if os.path.exists(path):
                        path = os.path.join(
                            folder,
                            datetime.datetime.strftime(datetime.datetime.now(), f"%Y_%m_%d__%H_%M__%f") + (f"__{log_details}" if log_details is not None else "") + ".log"
                            )

                    if not os.path.exists(folder):
                        os.mkdir(folder)
                    dhandler["filename"] = path

        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


@decorators.time_log
def newException(e, do_send_email=True):
    try:
        # new Exception for today
        template = loader.get_template("mail/admin/exception.html")
        subject = "Exception at {0}()".format(inspect.stack()[1][3])

        html_part = template.render({
            "subject": subject,
            "exception": e,
            "exceptionType": type(e),
            "traceback": traceback.format_exc()
        })

        if do_send_email:
            send_email(subject, html_part)
        else:
            logger.info(subject)
            logger.info(as_plain_text(html_part))

    except BaseException as e:
        logger.exception(e)


def getNextDocumentNumber(type):
    cfg_file_name = 'config_documentNo_local.ini'
    cfg = ConfigParser()
    cfg.optionxform = str
    try:
        cfg.read(cfg_file_name)
    except:
        logger.exception(f"Failed to read {cfg_file_name} file")
        1/0

    docNo = cfg.getint("documentNumbers", type)
    cfg.set("documentNumbers", type, str(docNo+1))

    with open(cfg_file_name, 'w') as configfile:
        cfg.write(configfile)

    return docNo


def retToFileArray(ret, filename):
    ret = ret[0]
    retCnt = len(ret)

    thefile = open(filename+".txt", 'w')
    for ctr, r in enumerate(ret, start=1):
        thefile.write("{}/{} - {}\n".format(ctr, retCnt, r))


def cfg_has_option(section, option):
    cfg_file_name = 'config_local.ini'

    cfg = ConfigParser()
    cfg.read(cfg_file_name)

    return cfg.has_option(section, option)


def cfg_has_section(section):
    cfg_file_name = 'config_local.ini'

    cfg = ConfigParser()
    cfg.read(cfg_file_name)

    return cfg.has_section(section)


@decorators.time_log
def getCfgVal(section, varName, retType=None):
    cfg_file_name = 'config_local.ini'

    cfg = ConfigParser()
    cfg.read(cfg_file_name)

    if retType == "int":
        ret = cfg.getint(section, varName)
    elif retType == "bool":
        ret = cfg.getboolean(section, varName)
    else:
        ret = cfg.get(section, varName)

    if section == "client" and varName in ['bccEmails', 'notificationEmails', ] \
    or section == "deliveryNote" and varName in ['sources', 'destinations'] \
    or section == "gesto" and varName in ['branches', ] \
    or section == "receptions" and varName in ['branches', ] \
    or section == "products" and varName in ['allowMissingDefaultGest', ]:
        ret = [x.strip() for x in ret.split(",")]

    logger.info("{}: {}".format(varName, ret))

    return ret


COMPANY_KEYS = ("firma", "companyName", "branches")


def parse_companies(raw):
    """[winmentor] companies este o lista JSON de firme WinMentor servite de acest deploy."""
    try:
        companies = json.loads(raw)
    except (TypeError, ValueError) as e:
        raise ValueError(f"[winmentor] companies nu este JSON valid: {e}")

    if not isinstance(companies, list) or len(companies) == 0:
        raise ValueError("[winmentor] companies trebuie sa fie o lista nevida de firme")

    for company in companies:
        for key in COMPANY_KEYS:
            if key not in company:
                raise ValueError(f"[winmentor] companies: lipseste cheia '{key}' din {company}")

        # fara branches nu exista filtru pe request-urile Gesto: firma preia rapoartele tuturor locatiilor,
        # corect doar cand e singura firma servita de acest deploy
        if not company["branches"] and len(companies) > 1:
            raise ValueError(f"[winmentor] companies: firma '{company['firma']}' nu are niciun branch")

    return companies


def expand_branches(companies, deploy_branches):
    """Firma unica fara branches serveste toate locatiile active din Gesto (getTokens):
    fiecare request Gesto se face cu tokenul locatiei, deci lista trebuie enumerata explicit."""
    for company in companies:
        if not company["branches"]:
            if not deploy_branches:
                raise ValueError(f"[winmentor] companies: firma '{company['firma']}' nu are niciun branch, iar Gesto nu are nicio locatie activa")

            company["branches"] = list(deploy_branches)

    return companies


@decorators.time_log
def get_companies():
    return parse_companies(getCfgVal("winmentor", "companies"))


def branches_query(branches):
    """Fragment de query string pentru filtrarea pe branch-uri a request-urilor Gesto."""
    if not branches:
        return ""

    return "&branches=" + ",".join(branches)


def filter_branches(cfg_branches, company_branches):
    """Sectiunile de config sunt globale; pastram doar branch-urile firmei curente.
    ConfigParser lowercase-uieste cheile sectiunilor, iar locatiile vin din Gesto cu numele lor real."""
    cfg_lower = {b.lower() for b in cfg_branches}

    return [b for b in company_branches if b.lower() in cfg_lower]


SCHEDULER_JOB_PREFIX = "scheduler:"

# campurile CronTrigger acceptate; o cheie necunoscuta e ignorata tacut de APScheduler,
# iar jobul cade pe orarul implicit in loc sa dea eroare
CRON_KEYS = ("minute", "hour", "day", "month", "day_of_week")

# cat asteapta scheduler-ul o rulare main.py inainte s-o considere intepenita;
# fiecare job isi poate pune alta valoare, in secunde
SCHEDULER_TIMEOUT = 600


def scheduler_schedule_path(cfg, app_dir):
    """Orarul sta intr-un fisier versionat, per firma (task_schedule/<firma>/scheduler.ini),
    ca sa nu se piarda odata cu config_local.ini, care nu e in git."""
    if not cfg.has_option("scheduler", "schedule_file"):
        raise ValueError("[scheduler]: lipseste 'schedule_file', calea catre orarul firmei")

    schedule_file = cfg.get("scheduler", "schedule_file")

    return os.path.join(app_dir, schedule_file)


def parse_scheduler_jobs(cfg):
    """Fiecare [scheduler:<nume>] e un job: argumentele date lui main.py plus orarul cron."""
    jobs = []

    for section in cfg.sections():
        if not section.startswith(SCHEDULER_JOB_PREFIX):
            continue

        options = dict(cfg.items(section))
        args = options.pop("args", "").split()

        if not args:
            raise ValueError(f"[{section}]: lipseste 'args', argumentele date lui main.py")

        if "timeout" in options:
            raise ValueError(f"[{section}]: 'timeout' e o valoare pentru tot orarul; muta-l in [scheduler]")

        for key in options:
            if key not in CRON_KEYS:
                raise ValueError(f"[{section}]: '{key}' nu este un camp cron valid; acceptate: {', '.join(CRON_KEYS)}")

        jobs.append({
            "name": section[len(SCHEDULER_JOB_PREFIX):],
            "args": args,
            "cron": options,
        })

    if not jobs:
        raise ValueError(f"config-ul nu contine niciun job [{SCHEDULER_JOB_PREFIX}<nume>]")

    return jobs


def scheduler_timeout(schedule):
    """Cat asteapta scheduler-ul o rulare inainte s-o considere intepenita, in secunde.

    E o singura valoare pentru tot orarul, si o folosesc amandoua capetele: scheduler-ul
    omoara rularea dupa ea, iar main.py se sprijina pe acelasi prag ca sa stie daca un
    DocImpServer.exe mai poate apartine unei rulari vii - peste prag, rularea care l-a
    pornit a fost deja omorata, deci serverul a ramas in urma."""
    raw = schedule.get("scheduler", "timeout", fallback=SCHEDULER_TIMEOUT)

    try:
        timeout = int(raw)
    except ValueError:
        raise ValueError(f"[scheduler]: 'timeout' se da in secunde, nu {raw!r}") from None

    if timeout <= 0:
        raise ValueError(f"[scheduler]: 'timeout' trebuie sa fie pozitiv, nu {timeout}")

    return timeout


def run_timeout(app_dir=APP_DIR):
    """Pragul din orar: acelasi cu care scheduler-ul opreste rularea.

    Un deploy fara orar - main.py pornit manual sau dintr-un task ramas in Task Scheduler -
    nu are de unde sa-l ia, deci primeste valoarea implicita."""
    try:
        cfg = ConfigParser()
        cfg.read_file(open(os.path.join(app_dir, "config_local.ini")))

        schedule = ConfigParser()
        schedule.read_file(open(scheduler_schedule_path(cfg, app_dir)))

        return scheduler_timeout(schedule)
    except (OSError, ValueError) as e:
        logger.info(f"orarul nu se poate citi, folosesc timeout-ul implicit: {e}")

        return SCHEDULER_TIMEOUT


BR_TAG = re.compile(r"<br\s*/?>", re.IGNORECASE)
BR_AT_EOL = re.compile(r"<br\s*/?>[ \t]*\n", re.IGNORECASE)
BLANK_LINES = re.compile(r"\n{3,}")
LAYOUT_LINES = re.compile(r"\n\s*\n+")

# marcaj pe prima linie a template-ului: randurile lui sunt marcate cu <br>, deci
# newline-urile lasate in urma de tag-uri sunt doar asezare in fisier, nu rand nou
FORMAT_PROPRIU = "<!-- formatare proprie -->"
INDENT = "    "


def as_email_html(msg):
    """Corpul pregatit pentru mail.

    Un template cu FORMAT_PROPRIU isi cere singur ruperile de rand, deci newline-urile lui
    nu se ating: sunt asezare in fisier, iar in HTML sunt spatiu alb. Ramane de rezolvat
    doar indentarea, pe care HTML-ul ar colapsa-o.

    Restul mesajelor sunt text construit in Python, unde newline-ul chiar inseamna rand nou."""
    if FORMAT_PROPRIU in msg:
        return msg.replace(FORMAT_PROPRIU, "").replace(INDENT, "&nbsp;" * 4)

    # exception.html isi tine randurile in <pre>; pana primeste si el marcajul, il recunoastem asa
    if "<html" in msg:
        return msg

    return msg.replace("\n", "<br/>")


def as_plain_text(rendered):
    """Corpul randat din template, curatat de taguri pentru log si pentru notificarile push.
    Mailul trimis de aici primeste in continuare HTML-ul; Gesto isi face singur conversia,
    deci lui ii dam tot textul.

    Cand textul poarta <br>, structura randurilor vine de acolo, iar newline-urile sunt
    doar asezare: blocurile {%if%} false si corpul fiecarui {% for %}, care include
    newline-ul de dupa tag, lasa altfel un rand gol intre elemente. Fara niciun <br>
    textul e construit in Python, unde randurile goale sunt puse intentionat.

    Un <br> la capat de rand nu adauga nimic, ruperea e deja acolo, deci consuma si
    newline-ul urmator; unul singur pe rand ramane rand gol.

    Tagurile inaintea entitatilor: invers, un &lt;b&gt; scris ca text in template
    ar deveni tag si ar fi sters."""
    text = LAYOUT_LINES.sub("\n", rendered) if BR_TAG.search(rendered) else rendered
    text = BR_TAG.sub("\n", BR_AT_EOL.sub("\n", text))
    text = html.unescape(strip_tags(text))

    # doar newline-urile: strip() ar manca si indentarea primului element
    return BLANK_LINES.sub("\n\n", text).strip("\n")


# print_args=False: decoratorul ar loga corpul brut, cu tagurile din template; functia
# il logheaza oricum mai jos, curatat
@decorators.time_log(print_args=False)
def send_email(subject, msg, toEmails=None, bccEmails=None, location=True, isGestoProblem=False):
    if not isGestoProblem:
        callersFrame = inspect.stack()[1][0]
    else:
        callersFrame = inspect.stack()[2][0]

    frameinfo = inspect.getframeinfo(callersFrame)

    msg = "\n" + msg
    if location:
        msg = "{}\n\n{}:{}".format(msg, frameinfo.filename, frameinfo.lineno)
    logger.info("msg: {}".format(as_plain_text(msg)))

    msg = as_email_html(msg)

    if toEmails is None or bccEmails is None:
        # create new list, if I ever append to it the value for settings.BCC_EMAILS will change and I will
        # send emails to people I don't want'
        bccEmailsCfg = getCfgVal("client", "bccEmails")

        if toEmails is None:
            toEmails = bccEmailsCfg
            logger.info("toEmails: {0}".format(toEmails))
        elif bccEmails is None:
            bccEmails = bccEmailsCfg
            logger.info(f"bccEmails: {bccEmails}")

    email_body = {
        "subject": subject,
        "body": msg,
        "emails": toEmails,
        "from_email": settings.DEFAULT_FROM_EMAIL,
    }

    # corpul e deja logat mai sus, lizibil; un repr de dict ar escapa newline-urile
    logger.info({k: v for k, v in email_body.items() if k != "body"})

    baseURL = getCfgVal("gesto", "url")
    token = getCfgVal("winmentor", "companyToken")

    r = SESSION.post(baseURL+"/api/email/", json=email_body, headers={'GESTOTOKEN': token})
    logger.info("{} - {}".format(r.status_code, r.text))


# print_args=False: vezi send_email
@decorators.time_log(print_args=False)
def report_problem(subject, body, hours, emails=None, verify_text=True):
    """Inregistreaza problema in Gesto (/api/gestoProblems/); True daca e noua in ultimele `hours` ore, deci merita un mail.

    Sub o ora, zecimalele sunt chiar minutele: 0.3 inseamna 30 de minute, 0.15 inseamna 15.

    Gesto dedubleaza pe subiect *si* pe corp. Cu verify_text=False dedubleaza doar pe subiect:
    pentru problemele al caror corp poarta un detaliu care se schimba la fiecare rulare - o
    durata, un contor - altfel fiecare raportare ar parea noua si ar trimite o notificare."""
    # Gesto trimite mailul cu replaceWithBR, deci face el conversia: \n devine <br/> si
    # cele patru spatii &nbsp;. Ii dam text simplu, ca sa o faca o singura data - corpul
    # randat, cu <br>-urile lui si cu newline-urile de asezare, ar iesi cu randurile dublate.
    body = as_plain_text(body)

    ngp_body = {
        "subject": subject,
        "body": body,
        "hours": hours,
        "verify_text": verify_text,
    }
    if emails is not None:
        ngp_body["emails"] = emails

    # corpul sub metadate: intr-un repr de dict newline-urile raman escapate
    meta = {k: v for k, v in ngp_body.items() if k != "body"}
    logger.info("{}\n{}".format(meta, body))

    baseURL = getCfgVal("gesto", "url")
    r = SESSION.post(baseURL + "/api/gestoProblems/", json=ngp_body)
    logger.info("{} - {}".format(r.status_code, r.text))

    return r.json()["ngp"]


def wmi_creation_datetime(raw):
    """CreationDate din WMI: YYYYMMDDHHMMSS.ffffff urmat de decalajul fata de UTC, in minute.

    Ora e deja cea a masinii, deci decalajul nu ne trebuie: il comparam cu datetime.now(),
    tot local."""
    return datetime.datetime.strptime(raw[:14], "%Y%m%d%H%M%S")


UNITATI = {
    "zi": ("zi", "zile"),
    "ora": ("ora", "ore"),
    "minut": ("minut", "minute"),
}


def numeral(count, unit):
    """In romana numeralul cere "de" cand ultimele doua cifre sunt cel putin 20:
    "3 minute", dar "40 de minute"."""
    singular, plural = UNITATI[unit]

    if count == 1:
        return f"1 {singular}"

    if count % 100 >= 20 or count % 100 == 0:
        return f"{count} de {plural}"

    return f"{count} {plural}"


def durata(minutes):
    """Unitatea creste cu durata, ca notificarea sa se citeasca dintr-o privire:
    4639 de minute nu spun nimic, trei zile spun tot."""
    if minutes == 0:
        return "sub un minut"

    if minutes >= 24 * 60:
        intreg, rest, unitate = minutes // (24 * 60), minutes % (24 * 60) // 60, ("zi", "ora")
    elif minutes >= 60:
        intreg, rest, unitate = minutes // 60, minutes % 60, ("ora", "minut")
    else:
        return numeral(minutes, "minut")

    if rest == 0:
        return numeral(intreg, unitate[0])

    return "{} si {}".format(numeral(intreg, unitate[0]), numeral(rest, unitate[1]))


def doc_imp_server_status(started_at, now):
    """Explicatia din corpul notificarii: cateva minute inseamna o rulare in curs,
    zile inseamna import intepenit."""
    if started_at is None:
        return "DocImpServer nu ruleaza."

    minutes = int((now - started_at).total_seconds() // 60)

    return f"DocImpServer ruleaza de {durata(minutes)}, din {started_at:%d.%m %H:%M}."


def defaultJSON(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, datetime.datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')


def getTimestamp(date):
    if isinstance(date, str):
        date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    elif not isinstance(date, datetime.datetime):
        date = datetime.datetime.combine(date, datetime.datetime.min.time())

    ret = int((date - datetime.datetime(1970, 1, 1)).total_seconds())
    return ret

def disable_logging(lvl = logging.DEBUG):
    """ Decorator

    """
    def actual_disable_logging(func):
        @functools.wraps(func)
        def wrapper(*args,**kwargs):
            logging.disable(lvl)
            result = func(*args,**kwargs)
            logging.disable(logging.NOTSET)
            return result
        return wrapper
    return actual_disable_logging


@disable_logging(logging.DEBUG)
def fixupCUI2(cui):
    """ Return a CUI or CNP or Serie/Nr CI in format fix, daca sirul de intrare
        corepunde:
        CUI: XXddddddd[d][d]
        CNP: ddddddddddddd
        Serie/Nr CI: XXdddddd
        @return: (Boolean, str): True daca sirul a putut fi fixuit plus sirul
                fixuit, false si sirul de intrare altfel

    """
    # Incearca CUI
    x = re.match("^\\s*([A-z]{2})?\\s*([0-9]{7,9})\\s*$", cui)
    if x:
        pref, no = x.groups()
        if no:
            pref = "RO" if pref is None else pref
            logger.debug("%s -> %s", cui, pref + no)

            return (True, pref + no)

    # Incearca CNP
    x = re.match("^\\s*([0-9]{13})\\s*$", cui)
    if x:
        no, = x.groups()
        if no:
            logger.debug("%s -> %s", cui, no)

            return (True, no)

    # Incearca Serie/Nr
    x = re.match("^\\s*([A-z]{2})?\\s*([0-9]{6})?\\s*$", cui)
    if x:
        serie, nr = x.groups()
        if nr:
            serie = "TM" if serie is None else serie
            logger.debug("%s -> %s", cui, serie + nr)

            return (True, serie + nr)

    return (False, cui)


@disable_logging(logging.DEBUG)
def fixupCUI(cui):
    """ Return a unique simbol that can identify the partener
        @return: (str): simbol that can identify the partener
    """

    ret = cui.replace(" ", "").lower()
    ret = ret.replace("ro", "")

    return ret


def log_json(myjson, indent=2):
    frames = traceback.extract_stack()
    frame = frames[-2]
    logger.info("{}:{}, {}()".format(frame.filename, frame.lineno, frame.name))

    logger.info(json.dumps(myjson, sort_keys=True, indent=indent, separators=(',', ': '), default=defaultJSON))


@decorators.time_log
def getTokens():
    import requests

    baseURL = getCfgVal("gesto", "url")
    token = getCfgVal("winmentor", "companyToken")
    url = baseURL + "/poses/?active=1"

    logger.info(url)

    r = SESSION.get(url, headers={'GESTOTOKEN': token})

    if r.status_code != 200:
        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
        1 / 0
    else:
        retJSON = r.json()
        log_json(retJSON)

        tokens = dict([(pos["branch"]["name"], str(pos["serialNum"])) for pos in retJSON["data"]])

        return tokens


@decorators.time_log
def send_push_notification(title, message, email=False, channel="gesto-push-general"):
    # tags can be all from here: https://docs.ntfy.sh/emojis/
    import requests
    headers = {
        "Title": title,
        "Priority": "urgent",
        "Tags": "warning"
    }
    URL = "https://ntfy.sh/" + channel

    if email:
        send_email(title, message)

    # doar ntfy primeste text simplu; mailul isi pastreaza formatarea
    SESSION.post(url=URL, data=as_plain_text(message), headers=headers)