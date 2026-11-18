"""Export the Board Boxes UI and a read-only snapshot of the QFBMS boards for Pages.

Based on the testing-BMS-designs exporter (content-hashed assets, bottom renders, per-board
schematics, part notes, hashed script URLs). QFBMS differences: an explicit board list
(rev-a/route/ holds scratch boards), the old board keeps its combined main + monitor
schematic, and the two published reference photos stay in the snapshot.
"""
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from part_notes import notes_for_board
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
UI = Path(__file__).resolve().parent
SITE = ROOT / 'site'
DATA = SITE / 'data'
FILES = SITE / 'files'
DATA.mkdir(exist_ok=True)
FILES.mkdir(exist_ok=True)
KICAD_CLI = r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'
KICAD_PY = r'C:\Program Files\KiCad\10.0\bin\python.exe'
BOARDS = ['rev-a/qfbms-rev-a.kicad_pcb', 'rev-a/qfbms-rev-a-visual.kicad_pcb', 'qfbms32.kicad_pcb',
          'exports/reconciliation-qa/qfbms32.kicad_pcb']
# Old board: main schematic + separate monitor project, published once (Nov 4) and kept as is.
OLD_SCHEMATIC = 'files/full-system-schematic.pdf'


def write_json(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')


assets = {}
def asset(relative):
    if relative in assets:
        return assets[relative]
    source = ROOT / relative
    # Named by content, not path: a new render gets a new URL, so no browser shows a cached old one.
    name = hashlib.sha256(source.read_bytes()).hexdigest()[:12] + source.suffix
    shutil.copyfile(source, DATA / name)
    assets[relative] = 'data/' + name
    return assets[relative]


def sanitize(value):
    """Machine-specific model resolution paths are not needed in a public snapshot."""
    if isinstance(value, dict):
        for key in ['resolved', 'alt_exists']:
            value.pop(key, None)
        for child in value.values():
            sanitize(child)
    elif isinstance(value, list):
        for child in value:
            sanitize(child)


boards = {}
for relative in BOARDS:
    source = ROOT / relative
    if not source.exists():
        continue
    result = subprocess.run([KICAD_PY, str(UI / 'kicad_bridge.py'), 'read', str(source)],
                            capture_output=True, text=True, encoding='utf-8', check=True)
    board = json.loads(result.stdout.split('@@JSON@@', 1)[1])
    board['path'] = relative
    board['partNotes'] = notes_for_board(relative, [f['ref'] for f in board.get('footprints', [])])
    sanitize(board)
    boxfile = source.with_suffix('.boxes.json')
    boxes = json.loads(boxfile.read_text(encoding='utf-8')) if boxfile.exists() else {}
    boxes['exists'] = boxfile.exists()
    renders = {}
    for kind in ['top', 'iso', 'bottom']:
        render = source.with_name(source.stem + '_3d_' + kind + '.png')
        entry = {'exists': render.exists()}
        if render.exists():
            image = render.relative_to(ROOT).as_posix()
            asset(image)
            entry.update(image=image, timestamp=datetime.datetime.fromtimestamp(render.stat().st_mtime).strftime('%b %d, %Y %H:%M'))
        renders[kind] = entry
    boards[relative] = dict(board=board, boxes=boxes, renders=renders)

    # Schematic PDF per board, published next to the snapshot.
    if relative.startswith('rev-a/'):
        # Both rev A boards (routed and the visual-only copy) share rev A's schematic.
        pdf = FILES / 'rev-a-schematic.pdf'
        subprocess.run([KICAD_CLI, 'sch', 'export', 'pdf', '-o', str(pdf), str(ROOT / 'rev-a/qfbms-rev-a.kicad_sch')],
                       check=True, capture_output=True)
        stamp = datetime.datetime.now().strftime('%B %d, %Y')
        rel_pdf = 'files/' + pdf.name
    else:
        pdf = SITE / OLD_SCHEMATIC
        stamp = 'November 4, 2026'
        rel_pdf = OLD_SCHEMATIC
    if pdf.exists():
        boards[relative]['schematic'] = dict(pdf=rel_pdf, pages=len(PdfReader(pdf).pages), timestamp=stamp)

# Stable copies for the News page (data/ names are content hashes and change).
for src, dst in [('rev-a/qfbms-rev-a_3d_top.png', 'rev-a-3d-top.png'),
                 ('rev-a/qfbms-rev-a_3d_iso.png', 'rev-a-3d-iso.png'),
                 ('rev-a/render/rev-a-bottom.png', 'rev-a-3d-bottom.png'),
                 ('rev-a/bom.csv', 'rev-a-bom.csv')]:
    if (ROOT / src).exists():
        shutil.copyfile(ROOT / src, FILES / dst)

# Reference photos the user chose to publish (unchanged from the earlier QFBMS export).
images = []
for relative in ['_reference/vfbms32_cad_top_reference_rotated.png', '_reference/vfbms32_real_bottom_hd.png']:
    if (ROOT / relative).exists():
        asset(relative)
        images.append(dict(path=relative, name=Path(relative).name, kb=round((ROOT / relative).stat().st_size / 1024)))
# TI's BQ76952 EVM schematic for the "TI Reference Schematic" button.
TI_EVM = '_reference/ti_bq76952/SLUC687A/sluc687/BQ76952EVM_BoardFiles/BMS029B(001)_Sch.PDF'
if (ROOT / TI_EVM).exists():
    asset(TI_EVM)
write_json(DATA / 'dashboard.json', dict(boards=boards, images=images, assets=assets))
# Content-named data files leave the previous export's copies behind; drop the ones no longer used.
used = {Path(p).name for p in assets.values()} | {'dashboard.json'}
for stale in DATA.iterdir():
    if stale.is_file() and stale.name not in used:
        stale.unlink()

shutil.copyfile(UI / 'style.css', SITE / 'style.css')
js = (UI / 'app.js').read_text(encoding='utf-8')
js = js.replace("'use strict';", "'use strict';\n  const fetch = window.dashboardFetch;")
js = re.sub(r'`/api/image\?path=\$\{encodeURIComponent\((\w+)\)\}(?:&t=\$\{Date.now\(\)\})?`', r'window.dashboardAsset(\1)', js)
js = js.replace('`/api/${pdfEndpoint}?path=${encodeURIComponent(S.boardPath)}&t=${Date.now()}`', 'window.dashboardSchematic(S.boardPath)')
js = js.replace('`/api/image?path=${encodeURIComponent(S.renderIsoPath)}&t=${Date.now()}`', 'window.dashboardAsset(S.renderIsoPath)')
js = js.replace('`saved · ${res.file.split(\'/\').pop()}`', "'saved in this browser'")
js = js.replace('with KiCad… (first load can take ~10 s)', 'from published snapshot…')
js = js.replace('Rendered ${res.timestamp}', 'Published snapshot · ${res.timestamp}')
(SITE / 'app.js').write_text(js, encoding='utf-8')

html = (UI / 'index.html').read_text(encoding='utf-8')
html = html.replace('<div class="actions">', '<div class="actions"><a class="btn btn-ghost btn-sm" href="news.html">News</a>')
html = html.replace('QFBMS PCB Dashboard</small>', 'QFBMS · published snapshot · saved in this browser</small>')
html = html.replace('<script src="app.js', '<script src="hosted.js"></script>\n  <script src="app.js')
if TI_EVM in assets:
    html = html.replace('/api/image?path=_reference/ti_bq76952/SLUC687A/sluc687/BQ76952EVM_BoardFiles/BMS029B%28001%29_Sch.PDF',
                        assets[TI_EVM])
# Pages lets browsers cache files for 10 minutes; a hash of each published file makes every change a new URL.
for name in ['style.css', 'hosted.js', 'app.js']:
    digest = hashlib.sha256((SITE / name).read_bytes()).hexdigest()[:10]
    html, count = re.subn(r'"' + re.escape(name) + r'(\?v=[^"]*)?"', f'"{name}?v={digest}"', html)
    assert count == 1, f'index.html should load {name} once, found {count}'
(SITE / 'index.html').write_text(html, encoding='utf-8')
print('Exported', len(boards), 'boards and', len(assets), 'assets')
