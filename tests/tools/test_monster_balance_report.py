import csv

from tools.monsters.balance_probe.report import write_report


def test_report_escapes_sources_and_blocks_external_artifact_links(tmp_path):
    write_report(
        tmp_path,
        {
            "players": {"p": {"name": "<script>alert(1)</script>", "skills": {}}},
            "cases": [
                {
                    "id": "<unsafe>",
                    "requested": 1,
                    "completed": 0,
                    "rejected": 1,
                    "files": {
                        "fights": "javascript:alert(1)",
                        "rosters": "../outside.json",
                        "monsters": "cases/monsters.json",
                    },
                }
            ],
            "metadata": {"limitations": ["<img onerror=alert(1)>"]},
        },
    )
    document = (tmp_path / "report.html").read_text(encoding="utf-8")
    assert "<script>" not in document
    assert "&lt;script&gt;" in document
    assert 'href="javascript:' not in document
    assert 'href="../' not in document
    assert 'href="cases/monsters.json"' in document
    with (tmp_path / "summary.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert rows[0]["completed"] == "0"
    assert rows[0]["rejected"] == "1"
