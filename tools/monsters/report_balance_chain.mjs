/** Build the Russian balance report from completed local simulation JSON.
 * Usage: bundled-node tools/monsters/report_balance_chain.mjs <summary.json> [output-directory]
 * Requires a node_modules junction to the bundled runtime inside output-directory.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

const sourcePath = path.resolve(process.argv[2] ?? 'var/balance-chain-goblin-sneak-2026-10-17/summary.json');
const outputDir = path.resolve(process.argv[3] ?? 'outputs/balance-chain-2026-10-17');
const source = JSON.parse(await fs.readFile(sourcePath, 'utf8'));
const require = createRequire(path.join(outputDir, 'package.json'));
const { Workbook, SpreadsheetFile } = await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const cases = source.cases;
if (!Array.isArray(cases) || !cases.length) throw new Error('No completed simulation cases');
const keys = new Set();
for (const c of cases) {
  const key = `${c.player_tier}-${c.monster_tier}-${c.monster_count}`;
  if (keys.has(key)) throw new Error(`Duplicate case ${key}`);
  keys.add(key);
  if (c.battles !== (c.wins.player ?? 0) + (c.wins.monster ?? 0) + (c.wins.draw ?? 0)) throw new Error(`Win counts do not reconcile: ${key}`);
}
const wb = Workbook.create();
const summary = wb.worksheets.add('Сводная');
const details = wb.worksheets.add('Серии');
const builds = wb.worksheets.add('Сборки');
const ink = '#203047', navy = '#24466B', muted = '#637185';
function base(sheet, extent) {
  sheet.showGridLines = false;
  sheet.getRange(extent).format.font = { name: 'Arial', size: 10, color: ink };
  sheet.getRange(extent).format.rowHeight = 22;
  sheet.getRange(extent).format.verticalAlignment = 'center';
  sheet.getRange(extent).format.columnWidth = 12;
}
function title(sheet, text) {
  sheet.getRange('A2').values = [[text]];
  sheet.getRange('A2').format.font = { name: 'Arial', size: 16, bold: true, color: ink };
  sheet.getRange('A3:H3').format.borders = { bottom: { style: 'thin', color: '#AEBECC' } };
}
function header(sheet, range) {
  sheet.getRange(range).format = { fill: navy, font: { name: 'Arial', size: 10, bold: true, color: '#FFFFFF' }, rowHeight: 30, wrapText: true, horizontalAlignment: 'center', verticalAlignment: 'center' };
}
base(summary, 'A1:U60'); base(details, `A1:P${cases.length + 8}`); base(builds, 'A1:U80');
summary.tabColor = navy;
title(summary, 'Баланс гоблинов: боец с двумя клинками');
summary.getRange('A4').values = [['Доля побед игрока. Пусто — серия не проводилась.']];
summary.getRange('A5').values = [[`По ${source.config.battles} боёв. Гоблин-миньон, одинаковые копии в отряде.`]];
summary.getRange('A6').values = [['2–5 гоблинов — обычный размер. 1 и 6 — диагностика.']];
summary.getRange('J5').values = [[source.status === 'complete' ? `Завершено: ${cases.length} серий, ${cases.reduce((s, c) => s + c.battles, 0)} боёв` : `Частичный расчёт: завершено ${cases.length} серий`]];
summary.getRange('A4:A6').format.font = { italic: true, color: muted };
summary.getRange('A8:H8').values = [['Тир игрока', 'Тир гоблина', '1 гоблин', '2 гоблина', '3 гоблина', '4 гоблина', '5 гоблинов', '6 гоблинов']];
header(summary, 'A8:H8');
summary.getRange('A:A').format.columnWidth = 15;
summary.getRange('B:B').format.columnWidth = 15;
summary.getRange('C:H').format.columnWidth = 12;
summary.getRange('I:I').format.columnWidth = 3;
summary.freezePanes.freezeRows(8);
details.getRange('A4').values = [[`Источник: ${path.relative(path.dirname(sourcePath), sourcePath)} и JSON отдельных серий. Снимок расчётов, не интерактивный симулятор.`]];
title(details, 'Результаты отдельных серий');
const headers = ['Тир игрока', 'Тир гоблина', 'Гоблинов', 'Размер отряда', 'Навыки игрока', 'Бои', 'Победы игрока', 'Победы гоблинов', 'Ничьи', 'Победы игрока, %', 'Медиана раундов', 'Остаток HP игрока', 'Убито гоблинов в среднем', 'Начальный seed', 'Серия'];
details.getRange('A6:O6').values = [headers]; header(details, 'A6:O6');
const caseRows = new Map();
cases.forEach((c, i) => {
  const row = i + 7;
  const min = c.official_squad_range?.min ?? 2, max = c.official_squad_range?.max ?? 5;
  const mastery = c.player_mastery;
  const values = [c.player_tier, c.monster_tier, c.monster_count, c.monster_count >= min && c.monster_count <= max ? 'Обычный' : 'Диагностика', mastery, c.battles, c.wins.player ?? 0, c.wins.monster ?? 0, c.wins.draw ?? 0, null, c.median_rounds, c.mean_remaining_hp?.player ?? null, c.mean_deaths?.monster ?? null, c.seed_start ?? null, path.basename(c.case_path ?? `p${c.player_tier}-m${c.monster_tier}-n${c.monster_count}`)];
  details.getRange(`A${row}:O${row}`).values = [values];
  details.getRange(`J${row}`).formulas = [[`=G${row}/F${row}`]];
  caseRows.set(`${c.player_tier}-${c.monster_tier}-${c.monster_count}`, row);
  if (i % 2 === 1) details.getRange(`A${row}:O${row}`).format.fill = '#F1F5F9';
});
details.getRange(`E7:E${cases.length + 6}`).setNumberFormat('0%');
details.getRange(`J7:J${cases.length + 6}`).setNumberFormat('0%');
details.getRange(`K7:M${cases.length + 6}`).setNumberFormat('0.0');
details.getRange('D:D').format.columnWidth = 17;
details.getRange('E:O').format.columnWidth = 17;
details.getRange('M:M').format.columnWidth = 22;
details.freezePanes.freezeRows(6);
details.tables.add(`A6:O${cases.length + 6}`, true, 'BalanceCases');
for (let p = 0; p <= 5; p++) for (let m = 0; m <= 5; m++) {
  const row = 9 + p * 6 + m;
  summary.getRange(`A${row}:B${row}`).values = [[p, m]];
  if (m === 0) summary.getRange(`A${row}:H${row}`).format.borders = { top: { style: 'thin', color: '#AEBECC' } };
  for (let n = 1; n <= 6; n++) {
    const detailRow = caseRows.get(`${p}-${m}-${n}`);
    if (detailRow) summary.getCell(row - 1, n + 1).formulas = [[`='Серии'!J${detailRow}`]];
  }
}
summary.getRange('C9:H44').setNumberFormat('0%');
summary.getRange('C9:H44').conditionalFormats.add('colorScale', { colors: ['#F0C0B9', '#FFF0BE', '#B5DACC'], thresholds: [0, 0.5, 1] });
summary.getRange('A47').values = [['Сопоставимые тиры: доля побед игрока по числу гоблинов']];
summary.getRange('A49:G49').values = [['Гоблинов', 'Игрок Т0', 'Игрок Т1', 'Игрок Т2', 'Игрок Т3', 'Игрок Т4', 'Игрок Т5']]; header(summary, 'A49:G49');
for (let n = 1; n <= 6; n++) {
  summary.getRange(`A${49 + n}`).values = [[n]];
  for (let p = 0; p <= 5; p++) {
    const r = caseRows.get(`${p}-${p}-${n}`);
    if (r) summary.getCell(48 + n, p + 1).formulas = [[`='Серии'!J${r}`]];
  }
}
summary.getRange('B50:G55').setNumberFormat('0%');
summary.getRange('J49:L49').values = [['Тир', '2 гоблина', '5 гоблинов']]; header(summary, 'J49:L49');
for (let p = 0; p <= 5; p++) {
  const row = 50 + p;
  summary.getRange(`J${row}`).values = [[`Т${p}`]];
  for (const [n, col] of [[2, 'K'], [5, 'L']]) {
    const r = caseRows.get(`${p}-${p}-${n}`);
    if (r) summary.getRange(`${col}${row}`).formulas = [[`='Серии'!J${r}`]];
  }
}
summary.getRange('K50:L55').setNumberFormat('0%');
const colors = ['#47668B', '#2B928B', '#8B67A6', '#D69043', '#B25B6C', '#4D7950'];
function chart(range, text, from, to) {
  const c = summary.charts.add('line', summary.getRange(range));
  c.title = text; c.titleTextStyle.typeface = 'Arial'; c.titleTextStyle.fontSize = 14;
  c.legend = { position: 'bottom', textStyle: { typeface: 'Arial', fontSize: 11 } };
  c.xAxis = { axisType: 'textAxis', textStyle: { typeface: 'Arial', fontSize: 11 } };
  c.yAxis = { numberFormatCode: '0%', numberFormatSourceLinked: false, textStyle: { typeface: 'Arial', fontSize: 11 } };
  c.series.items.forEach((s, i) => { s.line = { fill: colors[i], style: 'solid', width: 2 }; });
  c.setPosition(from, to);
}
chart('A49:G55', 'Победы против своего тира', 'J8', 'U25');
chart('J49:L55', 'Обычный отряд своего тира', 'J27', 'U44');
title(builds, 'Сборки и условия проверки');
const notes = [
  ['Монстр', 'Гоблин-миньон goblin_sneak. Отряд состоит из одинаковых копий.'],
  ['Игрок', 'Два клинка, полный комплект предметов соответствующего тира.'],
  ['Боевые навыки', 'Фехтование, два оружия, лёгкая броня: 20% на Т0, +10 п.п. за тир, 70% на Т5.'],
  ['Характеристики', 'Исходный набор игрока фиксирован. Итог меняется за счёт предметов и навыков.'],
  ['Поведение', 'Локальный AI. Без активных способностей и финтов. Триггеры предметов действуют.'],
  ['Размер отряда', 'Обычный профиль гоблинов: 2–5. Серии с 1 и 6 служат диагностикой.'],
  ['Ничья', 'Победитель не определён движком до лимита раундов или завершения серии.'],
  ['Переходы', 'Тир игрока повышается, когда проиграны все серии с 1–6 гоблинами без единой победы или ничьей, либо достигнут тир гоблина 5.'],
  ['Граница выводов', 'Серия измеряет эту сборку и AI. Сопротивление указано до подавления противником. Активные умения и смешанные отряды не проверялись.'],
  ['Повторение', 'Изменение ячеек не запускает бой. Повторите симулятор и заново соберите отчёт.'],
  ['Источник', path.relative(process.cwd(), sourcePath)],
];
builds.getRange('A5:B15').values = notes;
builds.getRange('A:A').format.columnWidth = 24;
builds.getRange('B:B').format.columnWidth = 100;
builds.getRange('A5:A15').format.font = { bold: true };
builds.getRange('B5:B15').format.wrapText = true;
builds.getRange('A5:B15').format.rowHeight = 32;
const attributes = ['strength', 'agility', 'endurance', 'intellect', 'memory', 'mental', 'perception', 'projection', 'prediction'];
const collected = new Map();
for (const c of cases) {
  const caseDir = path.resolve(path.dirname(sourcePath), c.case_path ?? `p${c.player_tier}-m${c.monster_tier}-n${c.monster_count}`);
  let inputs;
  try { inputs = JSON.parse(await fs.readFile(path.join(caseDir, 'inputs.json'), 'utf8')); }
  catch (error) { throw new Error(`Missing source build for ${c.case_id}: ${error.message}`); }
  for (const kind of ['player', 'monster']) {
    const tier = kind === 'player' ? c.player_tier : c.monster_tier;
    if (!collected.has(`${kind}-${tier}`)) collected.set(`${kind}-${tier}`, { kind, tier, ...inputs[kind] });
  }
}
builds.getRange('A18:P18').values = [['Сторона', 'Тир', 'Сила', 'Ловкость', 'Выносл.', 'Интеллект', 'Память', 'Ментал.', 'Восприятие', 'Проекция', 'Предвид.', 'HP расчёт', 'Урон основной руки', 'Физ. сопр.', 'Физ. подавл.', 'Навыки']]; header(builds, 'A18:P18');
const buildValues = [...collected.values()].sort((a, b) => (a.kind === 'player' ? 0 : 1) - (b.kind === 'player' ? 0 : 1) || a.tier - b.tier).map(b => {
  const v = b.preview_values ?? {};
  return [b.kind === 'player' ? 'Игрок' : 'Гоблин', b.tier, ...attributes.map(k => v[k] ?? null), v.hp ?? null, v.main_hand_damage_base ?? null, v.physical_resistance ?? null, v.physical_suppression ?? null, b.kind === 'player' ? source.config.player_mastery_by_tier[b.tier] : null];
});
if (buildValues.length) builds.getRange(`A19:P${18 + buildValues.length}`).values = buildValues;
builds.getRange('B:B').format.columnWidth = 12;
// Long notes use the otherwise empty upper-right area without widening the tier column.
builds.getRange('B5:B15').clear({ applyTo: 'contents' });
for (let i = 0; i < notes.length; i++) { builds.mergeCells(`B${5 + i}:P${5 + i}`); builds.getRange(`B${5 + i}`).values = [[notes[i][1]]]; }
builds.getRange('C:P').format.columnWidth = 13;
builds.getRange('L19:M40').setNumberFormat('0.0');
builds.getRange('N19:P40').setNumberFormat('0.0%');
// Exercise a real source input and restore it before the final calculation.
const originalWins = cases[0].wins.player ?? 0;
const changedWins = originalWins === cases[0].battles ? originalWins - 1 : originalWins + 1;
details.getRange('G7').values = [[changedWins]];
wb.recalculate();
const firstSummaryRow = 9 + cases[0].player_tier * 6 + cases[0].monster_tier;
const changedRate = summary.getCell(firstSummaryRow - 1, cases[0].monster_count + 1).values[0][0];
if (typeof changedRate !== 'number' || Math.abs(changedRate - changedWins / cases[0].battles) > 1e-10) throw new Error('Source-to-summary recalculation failed');
details.getRange('G7').values = [[originalWins]];
wb.recalculate();
const errors = await wb.inspect({ kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options: { useRegex: true, maxResults: 20 }, maxChars: 3000 });
await fs.mkdir(outputDir, { recursive: true });
await fs.writeFile(path.join(outputDir, 'verification.json'), JSON.stringify({ source: sourcePath, cases: cases.length, battles: cases.reduce((s, c) => s + c.battles, 0), formulaErrors: errors.ndjson, builds: buildValues.length, inputRecalculationVerified: true }, null, 2));
const inspected = await wb.inspect({ kind: 'table', range: 'Сводная!A8:H15', include: 'values,formulas', tableMaxRows: 8, tableMaxCols: 8, maxChars: 5000 });
await fs.writeFile(path.join(outputDir, 'summary-inspection.ndjson'), inspected.ndjson);
console.log(errors.ndjson);
for (const [sheetName, range, file] of [['Сводная', 'A1:U45', 'summary-preview.png'], ['Серии', `A1:O${Math.min(20, cases.length + 6)}`, 'cases-preview.png'], ['Сборки', 'A1:P32', 'builds-preview.png']]) {
  const preview = await wb.render({ sheetName, range, scale: 1.5, format: 'png' });
  await fs.writeFile(path.join(outputDir, file), new Uint8Array(await preview.arrayBuffer()));
}
const output = await SpreadsheetFile.exportXlsx(wb);
await output.save(path.join(outputDir, 'goblin-balance-chain.xlsx'));
console.log(JSON.stringify({ output: path.join(outputDir, 'goblin-balance-chain.xlsx'), cases: cases.length, builds: buildValues.length }));
