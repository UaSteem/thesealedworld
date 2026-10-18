"""Compact offline reports for reproducible monster balance probes."""

import csv
import html
import json
from pathlib import Path, PurePosixPath
from urllib.parse import quote

LABELS = {
    "ordinary": "Обычная встреча",
    "patrol": "Патруль",
    "guard": "Охрана",
    "leader": "Главарь",
    "fixed": "Фиксированный состав",
    "easy": "Лёгкая",
    "normal": "Средняя",
    "hard": "Тяжёлая",
    "both": "У обеих сторон",
    "none": "Без финтов",
    "player": "Только у игрока",
    "monsters": "Только у монстров",
}


def _text(value):
    return html.escape(str(value), quote=True)


def _number(value, digits=2):
    return "—" if value is None else f"{float(value):.{digits}f}".replace(".", ",")


def _percent(value):
    return "—" if value is None else f"{_number(value)}%"


def _link(path, label):
    """Only artifact-relative links; report data cannot inject active URLs."""
    path = str(path).replace("\\", "/")
    parsed = PurePosixPath(path)
    if not path or parsed.is_absolute() or ".." in parsed.parts or ":" in path:
        return ""
    return f'<a href="{quote(path, safe="/")}">{_text(label)}</a>'


def _distribution(value):
    if not value:
        return "—"
    labels = {"minion": "миньон", "veteran": "ветеран", "elite": "элита", "boss": "босс"}
    parts = []
    for key, count in sorted(value.items()):
        label = str(key)
        for source, target in labels.items():
            label = label.replace(source, target)
        parts.append(f"{_text(label)}: {_text(count)}")
    return "<br>".join(parts)


def write_report(output: Path, report: dict) -> None:
    """Write human-facing HTML and flat CSV; engine owns manifest and raw JSON."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    cases = report.get("cases", [])
    players = report.get("players", {})
    metadata = report.get("metadata", {})
    config = report.get("config", {})
    fields = (
        "id",
        "player_key",
        "mode",
        "encounter_type",
        "difficulty",
        "tier",
        "requested",
        "completed",
        "rejected",
        "player_wins",
        "monster_wins",
        "draws",
        "survived",
        "survival_percent",
        "mean_player_hp_percent",
        "mean_rounds",
        "min_count",
        "max_count",
        "feints_selected",
        "artifact_variant_count",
    )
    with (output / "summary.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(cases)

    player_rows = []
    regen_rows = []
    for key, player in players.items():
        skills = ", ".join(
            f"{name}: {_number(float(value) * 100, 1)}%" for name, value in player.get("skills", {}).items()
        )
        score = player.get("gear_score")
        if isinstance(score, dict):
            score = score.get("total")
        source = player.get("source", "—")
        if isinstance(source, dict):
            mode = source.get("mode")
            source = (
                f"Текущий стартовый слепок · {source.get('imprint_id', key)}"
                if mode == "live_starting_imprint"
                else f"Сохранённый снимок · {source.get('key', key)}"
                if mode == "saved_snapshot"
                else str(source)
            )
        player_rows.append(
            "<tr>"
            f"<th>{_text(player.get('name', key))}</th>"
            f"<td>{_text(source)}</td>"
            f"<td>{_number(score, 3)}</td>"
            f"<td>{_text(player.get('equipment_count', '—'))}</td>"
            f"<td>{_text(skills or '—')}</td></tr>"
        )
        regen = player.get("regen") or {}
        for mode, label in (("combat", "В бою"), ("outside", "Вне боя")):
            values = regen.get(mode) or {}
            regen_rows.append(
                f"<tr><th>{_text(player.get('name', key))}</th><td>{label}</td>"
                + "".join(f"<td>{_number(values.get(resource), 3)}</td>" for resource in ("hp", "en", "stamina"))
                + "</tr>"
            )

    rows, details = [], []
    for case in cases:
        encounter = "fixed" if case.get("mode") == "fixed" else case.get("encounter_type", "fixed")
        count_min, count_max = case.get("min_count"), case.get("max_count")
        count = "—" if count_min is None else str(count_min) if count_min == count_max else f"{count_min}–{count_max}"
        rows.append(
            "<tr>"
            f"<th>{_text(case.get('player_key', '—'))}</th>"
            f"<td>{_text(LABELS.get(encounter, encounter))}<br><small>{_text(LABELS.get(case.get('difficulty'), case.get('difficulty', '')))}</small></td>"
            f"<td>{_text(case.get('tier', '—'))}</td><td>{_text(count)}</td>"
            f"<td>{_text(case.get('player_wins', 0))}/{_text(case.get('completed', 0))}</td>"
            f"<td>{_percent(case.get('survival_percent'))}</td>"
            f"<td>{_percent(case.get('mean_player_hp_percent'))}</td>"
            f"<td>{_number(case.get('mean_rounds'))}</td>"
            f"<td>{_text(case.get('rejected', 0))}</td><td>{_text(case.get('draws', 0))}</td></tr>"
        )
        links = " · ".join(
            link
            for key, label in (("fights", "Каждый seed"), ("rosters", "Отряды"), ("monsters", "Слепки монстров"))
            if (link := _link(case.get("files", {}).get(key, ""), label))
        )
        details.append(
            f"<details><summary>{_text(case.get('id', 'Сценарий'))} — составы и артефакты</summary>"
            f"<p>{_distribution(case.get('rank_distribution'))}</p>"
            f"<p>Выбрано финтов: {_text(case.get('feints_selected', 0))}. "
            f"Вариантов в пуле: {_text(case.get('artifact_variant_count', '—'))}.</p>"
            f"<p>{links}</p></details>"
        )
    counts = {key: sum(case.get(key, 0) or 0 for case in cases) for key in ("requested", "completed", "rejected")}
    unchanged = metadata.get("source_before") == metadata.get("source_after") and bool(metadata.get("source_before"))
    status = (
        "Источники не изменились во время прогона" if unchanged else "Проверьте метаданные версии и состояние прогона"
    )
    warning = ""
    if metadata.get("skills_comparable") is False:
        warning = '<p class="notice">Навыки сборок различаются. Это сравнение билдов, а не изолированного влияния экипировки.</p>'
    limitations = metadata.get("limitations", [])
    if isinstance(limitations, str):
        limitations = [limitations]
    notes = "".join(f"<li>{_text(note)}</li>" for note in limitations)
    document = f"""<!doctype html>
<html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Проверка баланса монстров</title>
<style>
:root{{color-scheme:dark}}body{{font:15px/1.5 system-ui,sans-serif;background:#101722;color:#e4edf8;margin:0;padding:32px}}
main{{max-width:1440px;margin:auto}}h1{{font-size:28px;margin:0 0 8px}}h2{{font-size:20px;margin-top:30px}}
p{{max-width:1100px}}a{{color:#99ccff}}small,.muted{{color:#adbacb}}.scroll{{overflow:auto;border:1px solid #354357;border-radius:8px}}
table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}}th,td{{padding:11px 14px;border-bottom:1px solid #354357;text-align:left;vertical-align:top}}
thead{{background:#1c293a}}tbody tr:last-child>*{{border-bottom:0}}.metrics{{display:flex;gap:14px;flex-wrap:wrap;margin:24px 0}}
.metrics div{{background:#1a2637;border-radius:8px;padding:14px 22px}}.metrics strong{{display:block;font-size:24px}}
details{{border:1px solid #354357;border-radius:8px;padding:14px;margin:12px 0}}summary{{cursor:pointer;font-weight:600}}
pre{{overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere}}.notice{{border-left:3px solid #e9ba67;padding:12px;background:#302919}}
@media(max-width:700px){{body{{padding:16px}}th,td{{padding:8px}}}}
</style><main>
<h1>Проверка баланса монстров</h1>
<p class="muted">Воспроизводимый локальный прогон · {_text(metadata.get("status", "—"))} · {_text(status)}</p>
<p>Финты: {_text(LABELS.get(config.get("feints"), config.get("feints", "—")))}.
Режим: {_text(config.get("mode", "—"))}. Бои используют настоящий симулятор Combat; каталог и база данных не изменяются.</p>
<div class="metrics"><div><strong>{counts["requested"]}</strong>заказов</div><div><strong>{counts["completed"]}</strong>боёв</div><div><strong>{counts["rejected"]}</strong>отказов</div></div>
{warning}<h2>Игроки и навыки</h2><div class="scroll"><table><thead><tr><th>Сборка</th><th>Источник</th><th>GS</th><th>Предметов</th><th>Навыки</th></tr></thead><tbody>{"".join(player_rows)}</tbody></table></div>
<h2>Регенерация</h2><div class="scroll"><table><thead><tr><th>Сборка</th><th>Режим</th><th>HP</th><th>Энергия</th><th>Стамина</th></tr></thead><tbody>{"".join(regen_rows)}</tbody></table></div>
<h2>Результаты</h2><p>Победы и выживаемость считаются по состоявшимся боям. Отказы показаны отдельно. Средний остаток HP учитывает погибших как 0%.
Финты выбирает автоматическая политика; это не оценка ручной тактики игрока.</p>
<div class="scroll"><table><thead><tr><th>Сборка</th><th>Встреча</th><th>Тир монстров</th><th>Бойцов</th><th>Победы / бои</th><th>Выжили</th><th>Остаток HP</th><th>Раунды</th><th>Отказы</th><th>Ничьи</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<h2>Составы и исходные данные</h2>{"".join(details)}
<p>{_link("manifest.json", "Параметры и слепки для повторения")} · {_link("summary.json", "Полный JSON")} · {_link("summary.csv", "Таблица CSV")}</p>
<details><summary>Конфигурация и ограничения</summary><pre>{_text(json.dumps(config, ensure_ascii=False, indent=2))}</pre><ul>{notes}</ul>
<p>Математика: {_text(metadata.get("combat_math_version", "—"))}. Источник: {_text(metadata.get("source_before", "—"))}.</p></details>
</main></html>"""
    (output / "report.html").write_text(document, encoding="utf-8")
