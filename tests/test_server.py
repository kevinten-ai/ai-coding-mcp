import server


def test_main_runs_fastmcp_without_writing_to_stdout(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(server.mcp, "run", lambda: calls.append("run"))

    server.main()

    captured = capsys.readouterr()
    assert calls == ["run"]
    assert captured.out == ""
    assert "AI Coding MCP v2 starting" in captured.err
