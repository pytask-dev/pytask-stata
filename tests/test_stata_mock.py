from __future__ import annotations

import sys
import textwrap

from stata_mock.cli import _flatten_yaml
from stata_mock.cli import _parse_yaml_subset
from stata_mock.cli import main

NESTED_CHILD_LEVEL = 2


def test_yaml_read_with_locals_exposes_r_macros_and_saves_product(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "config.yaml"
    config.write_text(
        textwrap.dedent(
            """
            produces: out.dta
            database:
              host: localhost
              port: 5432
            debug: true
            """
        )
    )
    script = tmp_path / "script.do"
    script.write_text(
        textwrap.dedent(
            """
            args config
            yaml read using "`config'", locals replace
            save "`r(yaml_produces)'"
            """
        )
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["Stata", "-e", "do", script.as_posix(), config.as_posix(), "-mock"],
    )

    assert main() == 0
    assert (tmp_path / "out.dta").exists()
    assert "end of mock do-file" in (tmp_path / "mock.log").read_text()


def test_yaml_subset_matches_stata_for_supported_scalar_and_nested_types():
    config = textwrap.dedent(
        """
        string_value: hello
        integer_value: 42
        float_value: 3.14
        bool_true: true
        bool_false: false
        none_value: null
        path_value: build/output file.dta
        list_numbers:
        - 1
        - 2
        list_mixed:
        - 1
        - two
        - true
        - null
        nested_mapping:
          child_int: 1
          child_bool: false
          child_string: value
        """
    )

    entries = {entry.key: entry for entry in _flatten_yaml(_parse_yaml_subset(config))}

    assert entries["string_value"].value == "hello"
    assert entries["string_value"].type == "string"
    assert entries["integer_value"].value == "42"
    assert entries["integer_value"].type == "numeric"
    assert entries["float_value"].value == "3.14"
    assert entries["float_value"].type == "numeric"
    assert entries["bool_true"].value == "1"
    assert entries["bool_true"].type == "boolean"
    assert entries["bool_false"].value == "0"
    assert entries["bool_false"].type == "boolean"
    assert entries["none_value"].value == ""
    assert entries["none_value"].type == "null"
    assert entries["path_value"].value == "build/output file.dta"
    assert entries["path_value"].type == "string"

    assert entries["list_numbers"].type == "parent"
    assert entries["list_numbers_1"].value == "1"
    assert entries["list_numbers_1"].parent == "list_numbers"
    assert entries["list_numbers_1"].type == "list_item"
    assert entries["list_mixed_3"].value == "true"
    assert entries["list_mixed_3"].type == "list_item"
    assert entries["list_mixed_4"].value == "null"
    assert entries["list_mixed_4"].type == "list_item"

    assert entries["nested_mapping"].type == "parent"
    assert entries["nested_mapping_child_int"].value == "1"
    assert entries["nested_mapping_child_int"].level == NESTED_CHILD_LEVEL
    assert entries["nested_mapping_child_int"].parent == "nested_mapping"
    assert entries["nested_mapping_child_bool"].value == "0"
    assert entries["nested_mapping_child_bool"].type == "boolean"


def test_yaml_read_supports_custom_prefix_for_r_macros(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "config.yaml"
    config.write_text("produces: prefixed.dta\n")
    script = tmp_path / "script.do"
    script.write_text(
        textwrap.dedent(
            """
            args config
            yaml read using "`config'", locals prefix(cfg_) replace
            save "`r(cfg_produces)'"
            """
        )
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["Stata", "-e", "do", script.as_posix(), config.as_posix(), "-mock"],
    )

    assert main() == 0
    assert (tmp_path / "prefixed.dta").exists()


def test_yaml_get_returns_attributes_for_nested_mapping(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "config.yaml"
    config.write_text(
        textwrap.dedent(
            """
            database:
              host: localhost
              port: 5432
            """
        )
    )
    script = tmp_path / "script.do"
    script.write_text(
        textwrap.dedent(
            """
            args config
            yaml read using "`config'", replace
            yaml get database:host, quiet
            save "`r(host)'"
            """
        )
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["Stata", "-e", "do", script.as_posix(), config.as_posix(), "-mock"],
    )

    assert main() == 0
    assert (tmp_path / "localhost.dta").exists()


def test_yaml_get_returns_child_attributes_for_parent_key(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "config.yaml"
    config.write_text(
        textwrap.dedent(
            """
            indicators:
              CME_MRY0T4:
                label: mortality
                unit: deaths
                dataflow: CME
            """
        )
    )
    script = tmp_path / "script.do"
    script.write_text(
        textwrap.dedent(
            """
            args config
            yaml read using "`config'", replace
            yaml get indicators:CME_MRY0T4, attributes(label unit) quiet
            save "`r(label)'"
            """
        )
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["Stata", "-e", "do", script.as_posix(), config.as_posix(), "-mock"],
    )

    assert main() == 0
    assert (tmp_path / "mortality.dta").exists()


def test_yaml_validate_required_and_types_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "config.yaml"
    config.write_text(
        textwrap.dedent(
            """
            name: project
            version: 1
            debug: false
            """
        )
    )
    script = tmp_path / "script.do"
    script.write_text(
        textwrap.dedent(
            """
            args config
            yaml read using "`config'", replace
            yaml validate, required(name version debug) ///
                types(version:numeric debug:boolean)
            sysuse auto, clear
            """
        )
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["Stata", "-e", "do", script.as_posix(), config.as_posix(), "-mock"],
    )

    assert main() == 0
    assert "end of mock do-file" in (tmp_path / "mock.log").read_text()


def test_yaml_validate_required_failure_returns_stata_syntax_error(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "config.yaml"
    config.write_text("name: project\n")
    script = tmp_path / "script.do"
    script.write_text(
        textwrap.dedent(
            """
            args config
            yaml read using "`config'", replace
            yaml validate, required(name version)
            sysuse auto, clear
            """
        )
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["Stata", "-e", "do", script.as_posix(), config.as_posix(), "-mock"],
    )

    assert main() == 0
    assert "r(198)" in (tmp_path / "mock.log").read_text()


def test_yaml_read_rejects_unsupported_yaml_syntax(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "config.yaml"
    config.write_text("produces: &target out.dta\ncopy: *target\n")
    script = tmp_path / "script.do"
    script.write_text(
        textwrap.dedent(
            """
            args config
            yaml read using "`config'", locals replace
            save "`r(yaml_produces)'"
            """
        )
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["Stata", "-e", "do", script.as_posix(), config.as_posix(), "-mock"],
    )

    assert main() == 0
    assert "r(198)" in (tmp_path / "mock.log").read_text()
    assert not (tmp_path / "out.dta").exists()
