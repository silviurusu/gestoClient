import ast
import datetime
import pathlib
import re
from configparser import ConfigParser

import pytest
import requests
import urllib3

import util


VALID = '[{"firma": "CARMIC", "companyName": "CARMIC IMPEX SRL", "branches": ["c1", "c2"]}]'


def test_parse_companies_returns_list_of_dicts():
    companies = util.parse_companies(VALID)

    assert companies == [
        {"firma": "CARMIC", "companyName": "CARMIC IMPEX SRL", "branches": ["c1", "c2"]},
    ]


def test_parse_companies_rejects_invalid_json():
    with pytest.raises(ValueError, match="companies"):
        util.parse_companies('[{"firma": ')


def test_parse_companies_rejects_empty_list():
    with pytest.raises(ValueError, match="companies"):
        util.parse_companies("[]")


def test_parse_companies_rejects_missing_key():
    with pytest.raises(ValueError, match="branches"):
        util.parse_companies('[{"firma": "X", "companyName": "Y"}]')


def test_parse_companies_allows_empty_branches_for_single_company():
    assert util.parse_companies('[{"firma": "X", "companyName": "Y", "branches": []}]') == [
        {"firma": "X", "companyName": "Y", "branches": []},
    ]


def test_parse_companies_rejects_empty_branches_in_multi_company_deploy():
    with pytest.raises(ValueError, match="niciun branch"):
        util.parse_companies(
            '[{"firma": "X", "companyName": "Y", "branches": []},'
            ' {"firma": "Z", "companyName": "W", "branches": ["b1"]}]'
        )


def test_branches_query_joins_with_comma():
    assert util.branches_query(["c1", "c2"]) == "&branches=c1,c2"


def test_branches_query_is_empty_for_none():
    assert util.branches_query(None) == ""


def test_branches_query_is_empty_for_empty_list():
    assert util.branches_query([]) == ""


def test_filter_branches_keeps_only_company_branches():
    assert util.filter_branches(["b3", "b1", "b2"], ["b1", "b3"]) == ["b1", "b3"]


def test_filter_branches_matches_lowercased_config_keys_keeping_gesto_case():
    assert util.filter_branches(["pan partener", "corvin"], ["Pan Partener"]) == ["Pan Partener"]


def test_filter_branches_keeps_all_when_every_branch_is_in_config():
    assert util.filter_branches(["b1", "b2"], ["b1", "b2"]) == ["b1", "b2"]


def test_expand_branches_fills_single_company_with_all_deploy_branches():
    companies = [{"firma": "X", "companyName": "Y", "branches": []}]
    assert util.expand_branches(companies, ["b1", "b2"]) == [
        {"firma": "X", "companyName": "Y", "branches": ["b1", "b2"]},
    ]


def test_expand_branches_leaves_explicit_branches_untouched():
    companies = [{"firma": "X", "companyName": "Y", "branches": ["b1"]}]
    assert util.expand_branches(companies, ["b1", "b2"]) == [
        {"firma": "X", "companyName": "Y", "branches": ["b1"]},
    ]


def test_expand_branches_rejects_deploy_without_any_branch():
    with pytest.raises(ValueError, match="niciun branch"):
        util.expand_branches([{"firma": "X", "companyName": "Y", "branches": []}], [])


def scheduler_cfg(raw):
    cfg = ConfigParser()
    cfg.read_string(raw)

    return cfg


def test_parse_scheduler_jobs_returns_name_args_and_cron():
    jobs = util.parse_scheduler_jobs(scheduler_cfg(r"""
[scheduler]
python = C:\Python312\python.exe
working_dir = c:\Vectron\gestoClient

[scheduler:export]
args = --exportWinMentorData=1 --markedForWinMentorExport=1
hour = 6-21
minute = */5
"""))

    assert jobs == [
        {
            "name": "export",
            "args": ["--exportWinMentorData=1", "--markedForWinMentorExport=1"],
            "cron": {"hour": "6-21", "minute": "*/5"},
        },
    ]


def test_parse_scheduler_jobs_sends_a_per_job_timeout_to_the_right_place():
    """Timeout-ul e unul singur, pentru tot orarul; lasat in job ar trece drept camp cron."""
    with pytest.raises(ValueError, match=r"\[scheduler\]"):
        util.parse_scheduler_jobs(scheduler_cfg(r"""
[scheduler:export]
args = --exportWinMentorData=1
timeout = 120
"""))


def test_scheduler_timeout_reads_the_schedule_wide_value():
    assert util.scheduler_timeout(scheduler_cfg("[scheduler]\ntimeout = 120\n")) == 120


def test_scheduler_timeout_falls_back_when_not_set():
    assert util.scheduler_timeout(scheduler_cfg("[scheduler]\npython = x\n")) == util.SCHEDULER_TIMEOUT


def test_scheduler_timeout_rejects_a_value_that_is_not_a_number():
    with pytest.raises(ValueError, match="secunde"):
        util.scheduler_timeout(scheduler_cfg("[scheduler]\ntimeout = zece minute\n"))


def test_scheduler_timeout_rejects_a_value_that_is_not_positive():
    with pytest.raises(ValueError, match="pozitiv"):
        util.scheduler_timeout(scheduler_cfg("[scheduler]\ntimeout = 0\n"))


def test_parse_scheduler_jobs_rejects_unknown_cron_key():
    with pytest.raises(ValueError, match="minutes"):
        util.parse_scheduler_jobs(scheduler_cfg(r"""
[scheduler:export]
args = --exportWinMentorData=1
minutes = */5
"""))


def test_parse_scheduler_jobs_rejects_job_without_args():
    with pytest.raises(ValueError, match="args"):
        util.parse_scheduler_jobs(scheduler_cfg(r"""
[scheduler:export]
hour = 6-21
minute = */5
"""))


def test_parse_scheduler_jobs_rejects_empty_args():
    with pytest.raises(ValueError, match="args"):
        util.parse_scheduler_jobs(scheduler_cfg(r"""
[scheduler:export]
args =
minute = */5
"""))


def test_parse_scheduler_jobs_rejects_config_without_jobs():
    with pytest.raises(ValueError, match="scheduler:"):
        util.parse_scheduler_jobs(scheduler_cfg(r"""
[scheduler]
python = C:\Python312\python.exe
"""))


def test_parse_scheduler_jobs_keeps_config_order():
    jobs = util.parse_scheduler_jobs(scheduler_cfg(r"""
[scheduler:export]
args = --exportWinMentorData=1

[scheduler:trace_files]
args = --delete-old-trace-files=1 --days-ago=20
hour = 8
minute = 43
"""))

    assert [job["name"] for job in jobs] == ["export", "trace_files"]


def refuse_connections(monkeypatch, attempts):
    """Blocheaza stratul de socket, ca urllib3 sa vada acelasi esec de connect ca la o pana de DNS."""
    def refuse(*args, **kwargs):
        attempts.append(args)
        raise ConnectionRefusedError("nimeni nu asculta")

    monkeypatch.setattr(urllib3.util.connection, "create_connection", refuse)
    monkeypatch.setattr(urllib3.util.retry.time, "sleep", lambda _seconds: None)


def test_session_retries_connection_failures(monkeypatch):
    attempts = []
    refuse_connections(monkeypatch, attempts)

    with pytest.raises(requests.exceptions.ConnectionError):
        util.SESSION.get("https://www.gesto.ro/poses/")

    assert len(attempts) == util.CONNECT_RETRIES + 1


def test_session_retries_over_plain_http(monkeypatch):
    attempts = []
    refuse_connections(monkeypatch, attempts)

    with pytest.raises(requests.exceptions.ConnectionError):
        util.SESSION.get("http://www.gesto.ro/poses/")

    assert len(attempts) == util.CONNECT_RETRIES + 1


HTTP_VERBS = {"get", "post", "put", "patch", "delete", "head", "request"}


def bare_requests_calls(path):
    """Apelurile HTTP facute direct pe modulul `requests`, deci fara retry pe connect."""
    tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))

    return sorted(
        "{}:{} requests.{}".format(path, node.lineno, node.func.attr)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in HTTP_VERBS
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "requests"
    )


@pytest.mark.parametrize("path", ["main.py", "util.py", "winmentor.py", "maintenance.py"])
def test_http_calls_go_through_the_retrying_session(path):
    assert bare_requests_calls(path) == []


def test_scheduler_schedule_path_resolves_relative_to_app_dir():
    cfg = scheduler_cfg(r"""
[scheduler]
schedule_file = task_schedule\Carmic\scheduler.ini
""")

    assert util.scheduler_schedule_path(cfg, r"c:\Vectron\gestoClient") == r"c:\Vectron\gestoClient\task_schedule\Carmic\scheduler.ini"


def test_scheduler_schedule_path_keeps_absolute_path():
    cfg = scheduler_cfg(r"""
[scheduler]
schedule_file = d:\orare\carmic.ini
""")

    assert util.scheduler_schedule_path(cfg, r"c:\Vectron\gestoClient") == r"d:\orare\carmic.ini"


def test_scheduler_schedule_path_rejects_missing_key():
    cfg = scheduler_cfg(r"""
[scheduler]
python = C:\Python312\python.exe
""")

    with pytest.raises(ValueError, match="schedule_file"):
        util.scheduler_schedule_path(cfg, r"c:\Vectron\gestoClient")


@pytest.mark.parametrize("tag", ["<br>", "<br/>", "<br />", "<BR/>"])
def test_as_plain_text_turns_line_breaks_into_newlines(tag):
    assert util.as_plain_text(f"prima{tag}a doua") == "prima\na doua"


def test_as_plain_text_drops_the_other_tags_and_keeps_their_text():
    assert util.as_plain_text("<b>14011</b> --- SUMMER CROISSANT") == "14011 --- SUMMER CROISSANT"


def test_as_plain_text_leaves_text_without_tags_untouched():
    assert util.as_plain_text("APA MINERALA SAN GRAZIANO 0.375 L, 33017") == "APA MINERALA SAN GRAZIANO 0.375 L, 33017"


def test_as_plain_text_unescapes_entities_left_by_template_autoescape():
    assert util.as_plain_text("COCA COLA &amp; CO") == "COCA COLA & CO"


def test_as_plain_text_keeps_escaped_markup_as_text():
    """Un &lt;b&gt; scris ca text ramane text: entitatile se dezescapeaza dupa stergerea tagurilor."""
    assert util.as_plain_text("&lt;b&gt; nu e un tag") == "<b> nu e un tag"


def test_as_plain_text_collapses_runs_of_blank_lines():
    """Blocurile {%if%} false din template lasa in urma siruri de linii goale."""
    assert util.as_plain_text("prima\n\n\n\n\n\n\na doua") == "prima\n\na doua"


def test_as_plain_text_drops_leading_and_trailing_blank_lines():
    assert util.as_plain_text("\n\n\n\nUrmatoarele 4 coduri\n\n\n") == "Urmatoarele 4 coduri"


def test_as_email_html_does_not_touch_newlines_of_a_self_formatting_template():
    """Template-ul isi cere singur ruperile cu <br>; newline-urile lui sunt asezare in
    fisier, iar in HTML sunt spatiu alb - nu au ce strica."""
    msg = util.FORMAT_PROPRIU + "\nprima<br>\n\n\n    a doua<br>\n"

    assert util.as_email_html(msg) == "\nprima<br>\n\n\n" + "&nbsp;" * 4 + "a doua<br>\n"


def test_as_email_html_turns_indentation_into_nbsp():
    """HTML colapseaza spatiile; fara &nbsp; alinierea listelor s-ar pierde."""
    msg = util.FORMAT_PROPRIU + "\n    APA MINERALA, 33017<br>\n"

    assert util.as_email_html(msg) == "\n" + "&nbsp;" * 4 + "APA MINERALA, 33017<br>\n"


def test_as_email_html_turns_newlines_into_breaks_for_plain_text():
    assert util.as_email_html("prima\na doua") == "prima<br/>a doua"


def test_as_email_html_leaves_a_full_html_document_alone():
    """exception.html isi tine randurile in <pre>; pana primeste si el marcajul,
    documentul complet e recunoscut dupa <html."""
    msg = "<html><body><pre>prima\na doua</pre></body></html>"

    assert util.as_email_html(msg) == msg


def self_formatting_templates():
    folder = pathlib.Path(__file__).parent / "templates" / "mail" / "admin"

    return sorted(p for p in folder.glob("*.html") if util.FORMAT_PROPRIU in p.read_text(encoding="utf-8"))


TAG_ONLY = re.compile(r"^\s*\{%.*%\}\s*$")
COMMENT_ONLY = re.compile(r"^\s*<!--.*-->\s*$")


def test_there_are_self_formatting_templates_to_check():
    """Daca lista e goala, testul de mai jos ar trece degeaba."""
    assert self_formatting_templates()


@pytest.mark.parametrize("path", self_formatting_templates())
def test_self_formatting_template_ends_every_visible_line_with_a_break(path):
    """Randurile cu tag-uri emit doar spatiu alb; fiecare rand care chiar apare in mail
    trebuie sa-si ceara singur ruperea, altfel HTML-ul il lipeste de urmatorul."""
    unmarked = [
        line for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
        and not TAG_ONLY.match(line)
        and not COMMENT_ONLY.match(line)
        and not line.rstrip().endswith("<br>")
    ]

    assert unmarked == []


def test_as_plain_text_drops_the_blank_lines_left_by_loop_tags():
    """Corpul unui {% for %} include newline-ul de dupa tag, deci fiecare iteratie emite
    un rand gol inaintea elementului. Randurile goale adevarate sunt cele scrise <br>."""
    rendered = "\n    A, 33017<br>\n\n    B, 33016<br>\n<br>\nUrmatoarea sectiune<br>\n"

    assert util.as_plain_text(rendered) == "    A, 33017\n    B, 33016\n\nUrmatoarea sectiune"


def test_as_plain_text_keeps_the_indentation_of_the_first_line():
    assert util.as_plain_text("\n    APA MINERALA, 33017<br>\n") == "    APA MINERALA, 33017"


def test_as_plain_text_does_not_double_a_break_at_end_of_line():
    """<br> la capat de rand nu adauga nimic: ruperea e deja acolo. Singur pe rand, ramane rand gol."""
    assert util.as_plain_text("A<br>\nB<br>\n<br>\nC<br>\n") == "A\nB\n\nC"


def test_as_plain_text_on_a_rendered_template_fragment():
    rendered = "Urmatoarele 1 coduri nu apar in WinMentor:<br>\n    <b>2091</b> --- TORT, 2091<br>\n"

    assert util.as_plain_text(rendered) == "Urmatoarele 1 coduri nu apar in WinMentor:\n    2091 --- TORT, 2091"


def test_wmi_creation_datetime_reads_the_local_time():
    """CreationDate din WMI e deja in ora masinii; sufixul e doar decalajul ei fata de UTC."""
    assert util.wmi_creation_datetime("20260827143005.123456+180") == datetime.datetime(2026, 8, 27, 14, 30, 5)


def test_wmi_creation_datetime_handles_a_negative_offset():
    assert util.wmi_creation_datetime("20260101000000.000000-300") == datetime.datetime(2026, 1, 1, 0, 0, 0)


STARTED = datetime.datetime(2026, 8, 24, 9, 12, 0)


@pytest.mark.parametrize("now, expected", [
    (datetime.datetime(2026, 8, 24, 9, 15, 30), "de 3 minute"),
    (datetime.datetime(2026, 8, 24, 9, 52, 0), "de 40 de minute"),
    (datetime.datetime(2026, 8, 24, 11, 42, 0), "de 2 ore si 30 de minute"),
    (datetime.datetime(2026, 8, 27, 14, 31, 0), "de 3 zile si 5 ore"),
])
def test_doc_imp_server_status_scales_the_unit(now, expected):
    """Minute pentru o rulare in curs, zile pentru un import intepenit - la fel de citibil."""
    assert util.doc_imp_server_status(STARTED, now) == f"DocImpServer ruleaza {expected}, din 24.08 09:12."


@pytest.mark.parametrize("minutes, expected", [
    (0, "sub un minut"),
    (1, "1 minut"),
    (61, "1 ora si 1 minut"),
    (25 * 60, "1 zi si 1 ora"),
])
def test_durata_uses_the_singular(minutes, expected):
    assert util.durata(minutes) == expected


@pytest.mark.parametrize("minutes, expected", [
    (120, "2 ore"),
    (48 * 60, "2 zile"),
])
def test_durata_drops_a_zero_remainder(minutes, expected):
    """Un rest zero nu adauga nimic: "2 ore", nu "2 ore si 0 de minute"."""
    assert util.durata(minutes) == expected


def test_doc_imp_server_status_says_when_it_is_not_running():
    assert util.doc_imp_server_status(None, datetime.datetime(2026, 8, 27, 14, 30)) == "DocImpServer nu ruleaza."


ORAR = """
[scheduler]
timeout = 120

[scheduler:export]
args = --exportWinMentorData=1
minute = */5
"""


def deploy_cu_orar(tmp_path, orar, config="[scheduler]\nschedule_file = task_schedule/firma.ini\n"):
    """Un folder de aplicatie ca pe server: config_local.ini arata spre orar, printr-o cale
    relativa la folderul aplicatiei."""
    (tmp_path / "config_local.ini").write_text(config)

    if orar is not None:
        (tmp_path / "task_schedule").mkdir()
        (tmp_path / "task_schedule" / "firma.ini").write_text(orar)

    return str(tmp_path)


def test_run_timeout_reads_the_value_from_the_schedule(tmp_path):
    """main.py si watchdog-ul se sprijina pe acelasi prag cu care scheduler-ul opreste rularea."""
    assert util.run_timeout(deploy_cu_orar(tmp_path, ORAR)) == 120


def test_run_timeout_falls_back_without_a_schedule(tmp_path):
    """Deploy fara scheduler: main.py e pornit din Task Scheduler si n-are orar de citit."""
    app_dir = deploy_cu_orar(tmp_path, None, config="[scheduler]\npython = x\n")

    assert util.run_timeout(app_dir) == util.SCHEDULER_TIMEOUT


def test_run_timeout_falls_back_when_the_schedule_is_broken(tmp_path):
    """Un orar stricat nu trebuie sa opreasca rularea: pragul e o precautie, nu scopul ei."""
    assert util.run_timeout(deploy_cu_orar(tmp_path, "[scheduler]\ntimeout = maine\n")) == util.SCHEDULER_TIMEOUT


def test_run_timeout_falls_back_without_a_local_config(tmp_path):
    assert util.run_timeout(str(tmp_path)) == util.SCHEDULER_TIMEOUT

ORAR_CU_FEREASTRA = """
[scheduler:export]
args = --exportWinMentorData=1
hour = 6-22
minute = */5
"""


def test_run_cutoff_cere_o_rulare_incheiata_de_un_pas_de_orar(tmp_path):
    """Pasul e de 5 minute, plus marja pentru durata rularii: fereastra iese de 10."""
    app_dir = deploy_cu_orar(tmp_path, ORAR_CU_FEREASTRA)
    now = datetime.datetime(2026, 8, 27, 10, 3)

    assert util.run_cutoff(now, app_dir) == datetime.datetime(2026, 8, 27, 9, 53)


def test_run_cutoff_creste_fereastra_pentru_un_orar_mai_rar(tmp_path):
    """Un orar la 15 minute are nevoie de o fereastra mai larga, altfel cea mai recenta
    rulare incheiata iese din ea cat timp ruleaza urmatoarea."""
    app_dir = deploy_cu_orar(tmp_path, r"""
[scheduler:export]
args = --exportWinMentorData=1
hour = 6-21
minute = 0,15,30,45
""")
    now = datetime.datetime(2026, 8, 27, 12, 3)

    assert util.run_cutoff(now, app_dir) == datetime.datetime(2026, 8, 27, 11, 43)


def test_run_cutoff_tace_noaptea(tmp_path):
    """Orarul nu tine toata ziua: lipsa unei rulari incheiate e programul, nu un blocaj."""
    app_dir = deploy_cu_orar(tmp_path, ORAR_CU_FEREASTRA)

    assert util.run_cutoff(datetime.datetime(2026, 8, 27, 2, 3), app_dir) is None


def test_run_cutoff_tace_dupa_ultima_rulare_a_zilei(tmp_path):
    """La 23:07 ultima pornire a fost la 22:55: de aici incolo watchdog-ul n-ar mai gasi
    niciun log proaspat, si ar suna pana dimineata."""
    app_dir = deploy_cu_orar(tmp_path, ORAR_CU_FEREASTRA)

    assert util.run_cutoff(datetime.datetime(2026, 8, 27, 23, 7), app_dir) is None


def test_run_cutoff_ignora_pornirea_din_minutul_curent(tmp_path):
    """La 06:00 prima rulare a zilei abia porneste, iar inaintea ei nu e niciuna incheiata:
    numarata ca pornire, ar da o alarma falsa in fiecare dimineata."""
    app_dir = deploy_cu_orar(tmp_path, ORAR_CU_FEREASTRA)

    assert util.run_cutoff(datetime.datetime(2026, 8, 27, 6, 0, 30), app_dir) is None


def test_run_cutoff_nu_stramteaza_fereastra_pentru_doua_joburi_apropiate(tmp_path):
    """Curatarea fisierelor de trace e tot o rulare main.py, si cade la 3 minute dupa export.
    Pasul dintre ele nu trebuie sa string fereastra: rularea de la 08:40 poate fi inca in
    curs la 08:43, iar cea de dinaintea ei trebuie sa incapa in fereastra."""
    app_dir = deploy_cu_orar(tmp_path, ORAR_CU_FEREASTRA + r"""
[scheduler:trace_files]
args = --delete-old-trace-files=1 --days-ago=20
hour = 8
minute = 43
""")
    now = datetime.datetime(2026, 8, 27, 8, 45)

    assert util.run_cutoff(now, app_dir) == datetime.datetime(2026, 8, 27, 8, 35)


def test_run_cutoff_cade_pe_fereastra_implicita_fara_orar(tmp_path):
    """Fara orar - rularile pornite din Task Scheduler - watchdog-ul nu are de unde sti
    pasul: o alarma in plus e mai buna decat una pierduta."""
    app_dir = deploy_cu_orar(tmp_path, None, config="""
[scheduler]
python = x
""")
    now = datetime.datetime(2026, 8, 27, 2, 3)

    assert util.run_cutoff(now, app_dir) == now - util.RUN_MAX_AGE


def test_run_cutoff_cade_pe_fereastra_implicita_cand_orarul_n_are_joburi(tmp_path):
    app_dir = deploy_cu_orar(tmp_path, """
[scheduler]
timeout = 120
""")
    now = datetime.datetime(2026, 8, 27, 2, 3)

    assert util.run_cutoff(now, app_dir) == now - util.RUN_MAX_AGE


def orar_firma(firma):
    """Chiar orarul care ajunge pe serverul firmei, indexat dupa numele jobului."""
    cale = pathlib.Path(util.APP_DIR) / "task_schedule" / firma / "scheduler.ini"

    cfg = ConfigParser()
    cfg.read_string(cale.read_text(encoding="utf8"))

    return {job["name"]: job for job in util.parse_scheduler_jobs(cfg)}


def minute_declansate(cron, ora=9):
    """Minutele in care jobul chiar porneste, intr-o ora data.

    Le cerem trigger-ului, nu expresiei: "*/2" pare sa spuna "din doua in doua", dar
    inseamna minutele pare, deci fara 15 - exact capcana pe care o pazesc testele astea."""
    from apscheduler.triggers.cron import CronTrigger

    trigger = CronTrigger(timezone=util.TIMEZONE, **cron)
    inceput = datetime.datetime(2026, 8, 27, ora, 0)

    minute = []
    fire = trigger.get_next_fire_time(None, inceput)

    while fire is not None and fire.hour == ora:
        minute.append(fire.minute)
        fire = trigger.get_next_fire_time(fire, fire)

    return minute


def test_orarul_pan_partener_recupereaza_avizele_pe_minutul_15():
    """importAvize ia ziua curenta; o data pe ora ia mai multe, ca sa prinda ce a scapat.
    Cate zile si la ce minut spune orarul, nu minutul la care s-a nimerit sa porneasca."""
    recuperare = orar_firma("Pan Partener")["export_avize_6_zile"]

    assert "--days-ago=6" in recuperare["args"]
    assert minute_declansate(recuperare["cron"]) == [15]


def test_orarul_pan_partener_nu_porneste_doua_rulari_pe_acelasi_minut():
    """Pe minutul 15 ruleaza doar recuperarea: a doua rulare pornita in aceeasi clipa ar
    gasi DocImpServer ocupat si s-ar retrage fara sa exporte nimic."""
    assert 15 not in minute_declansate(orar_firma("Pan Partener")["export"]["cron"])


def test_orarul_pan_partener_pastreaza_cadenta_de_doua_minute():
    """Aceeasi cadenta ca in task-ul pe care il inlocuieste: din doua in doua minute,
    pornind de la minut impar."""
    minute = minute_declansate(orar_firma("Pan Partener")["export"]["cron"])

    assert minute[0] == 1
    assert all(m % 2 for m in minute)


def test_orarul_pan_partener_nu_ia_avize_seara():
    """Task-ul de seara pe care il inlocuieste rula fara --importAvize; avizele le ia doar
    fereastra de zi, iar recuperarea pe 6 zile cade tot in ea."""
    joburi = orar_firma("Pan Partener")

    assert "--importAvize=1" not in joburi["export_seara"]["args"]
    assert minute_declansate(joburi["export_seara"]["cron"], ora=17) == []
    assert minute_declansate(joburi["export"]["cron"], ora=20) == []
    assert minute_declansate(joburi["export_avize_6_zile"]["cron"], ora=20) == []
