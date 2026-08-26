import ast
import pathlib
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


def test_as_plain_text_on_a_rendered_template_fragment():
    rendered = "Urmatoarele 1 coduri nu apar in WinMentor:<br />\n    <b>2091</b> --- TORT, 2091"

    assert util.as_plain_text(rendered) == "Urmatoarele 1 coduri nu apar in WinMentor:\n\n    2091 --- TORT, 2091"
