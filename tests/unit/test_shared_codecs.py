from __future__ import annotations

from app.shared.codecs import dump_json, hash_password, load_json_list, load_json_object


def test_load_json_object_returns_dict_for_valid_object_text() -> None:
    assert load_json_object('{"a": 1, "b": "x"}') == {"a": 1, "b": "x"}


def test_load_json_object_returns_empty_dict_for_invalid_or_non_object_payload() -> None:
    assert load_json_object("") == {}
    assert load_json_object("[]") == {}
    assert load_json_object("{invalid}") == {}


def test_load_json_list_filters_non_dict_items() -> None:
    assert load_json_list('[{"id": "1"}, 2, "x", {"id": "2"}]') == [{"id": "1"}, {"id": "2"}]


def test_dump_json_preserves_unicode_without_ascii_escape() -> None:
    assert dump_json({"name": "总管理员"}) == '{"name": "总管理员"}'
