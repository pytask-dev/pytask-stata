from __future__ import annotations

from pytask import build


def test_marker_is_configured(tmp_path):
    session = build(paths=tmp_path)

    assert "stata" in session.config
    assert "stata" in session.config["markers"]
