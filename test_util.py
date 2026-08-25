import pytest

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
