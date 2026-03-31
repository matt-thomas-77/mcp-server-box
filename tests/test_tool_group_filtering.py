from config import _parse_csv_env_set
from server import TOOL_GROUP_REGISTRARS, _get_enabled_registrars


def test_parse_csv_env_set_normalizes_values():
    parsed = _parse_csv_env_set(" AI, doc_gen ,shared_link,,AI ")

    assert parsed == {"ai", "doc_gen", "shared_link"}


def test_get_enabled_registrars_disables_requested_groups():
    registrars = _get_enabled_registrars({"ai", "doc_gen"})

    expected = [
        registrar
        for group_name, registrar in TOOL_GROUP_REGISTRARS.items()
        if group_name not in {"ai", "doc_gen"}
    ]
    assert registrars == expected


def test_get_enabled_registrars_ignores_unknown_groups():
    registrars = _get_enabled_registrars({"not_a_group"})

    assert registrars == list(TOOL_GROUP_REGISTRARS.values())


def test_get_enabled_registrars_enable_only_specified_groups():
    registrars = _get_enabled_registrars(set(), enabled_groups={"search", "file"})

    expected = [
        registrar
        for group_name, registrar in TOOL_GROUP_REGISTRARS.items()
        if group_name in {"search", "file"}
    ]
    assert registrars == expected


def test_get_enabled_registrars_enable_takes_precedence_over_disable():
    registrars = _get_enabled_registrars(
        {"search"}, enabled_groups={"search", "file"}
    )

    expected = [
        registrar
        for group_name, registrar in TOOL_GROUP_REGISTRARS.items()
        if group_name in {"search", "file"}
    ]
    assert registrars == expected


def test_get_enabled_registrars_enable_ignores_unknown_groups():
    registrars = _get_enabled_registrars(set(), enabled_groups={"search", "not_real"})

    expected = [
        registrar
        for group_name, registrar in TOOL_GROUP_REGISTRARS.items()
        if group_name in {"search"}
    ]
    assert registrars == expected
