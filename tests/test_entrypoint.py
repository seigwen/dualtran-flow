import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main


def test_argv_mode_serves_the_query(monkeypatch, capsys):
    """Flow Launcher launches Python plugins with the JSON request in argv[1]."""
    monkeypatch.setattr(main, "query", lambda text: [{"Title": text}])
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", json.dumps({"method": "query", "parameters": ["hello"], "id": 7})],
    )

    main.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == 7
    assert payload["result"] == [{"Title": "hello"}]


def test_stdin_mode_still_works(monkeypatch, capsys):
    monkeypatch.setattr(main, "query", lambda text: [{"Title": text}])
    monkeypatch.setattr(sys, "argv", ["main.py"])
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(json.dumps({"method": "query", "parameters": ["hi"], "id": 8}) + "\n"),
    )

    main.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == 8
    assert payload["result"] == [{"Title": "hi"}]
