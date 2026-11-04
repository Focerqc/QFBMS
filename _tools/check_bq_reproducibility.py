"""Verify deterministic BQ sheets and regeneration without ignored inputs."""
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('qfbms32-bq-lower.kicad_sch', 'qfbms32-bq-upper.kicad_sch',
         'qfbms32-bq-startup.kicad_sch', 'qfbms32-bq-iso-i2c.kicad_sch', 'qfbms32-bq-monitors.kicad_sch')


def snapshot(directory):
    return {name: (directory / name).read_bytes() for name in NAMES}


def run(directory):
    subprocess.run([sys.executable, str(directory / '_tools/gen_bq_monitor_sheets.py')],
                   cwd=directory, check=True, stdout=subprocess.DEVNULL)


def main():
    expected = snapshot(ROOT)
    with tempfile.TemporaryDirectory(prefix='qfbms-bq-repro-') as directory:
        clean = Path(directory)
        (clean / '_tools').mkdir()
        for name in ('gen_bq_monitor_sheets.py', 'bq-monitor-identities.json'):
            shutil.copyfile(ROOT / '_tools' / name, clean / '_tools' / name)
        run(clean)
        first = snapshot(clean)
        run(clean)
        assert first == snapshot(clean), 'second generation changed bytes'
        assert first == expected, 'checked-in sheets differ from clean regeneration'
        for name, data in first.items():
            print(hashlib.sha256(data).hexdigest(), name)
    print('PASS: clean inputs reproduce all five sheets; second run is byte-identical')


if __name__ == '__main__':
    main()
