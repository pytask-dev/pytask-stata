from __future__ import annotations

import sys
import textwrap

from stata_mock.cli import main


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
