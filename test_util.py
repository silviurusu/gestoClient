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


def test_parse_companies_rejects_empty_branches():
    with pytest.raises(ValueError, match="niciun branch"):
        util.parse_companies('[{"firma": "X", "companyName": "Y", "branches": []}]')


def test_branches_query_joins_with_comma():
    assert util.branches_query(["c1", "c2"]) == "&branches=c1,c2"


def test_branches_query_is_empty_for_none():
    assert util.branches_query(None) == ""


def test_branches_query_is_empty_for_empty_list():
    assert util.branches_query([]) == ""


def test_filter_branches_keeps_only_company_branches_in_config_order():
    assert util.filter_branches(["b3", "b1", "b2"], ["b1", "b3"]) == ["b3", "b1"]


def test_filter_branches_is_identity_for_single_company_deploy():
    assert util.filter_branches(["b1", "b2"], ["b1", "b2"]) == ["b1", "b2"]
