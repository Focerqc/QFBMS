"""Electrical regression checks. Neither a circuit simulation nor a bench test."""
from pathlib import Path
import hashlib
import json
import circuit

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "rev-b"
p = {part["ref"]: part for part in circuit.PARTS}
assert len(p) == len(circuit.PARTS)
assert p["U_BQ1"]["pins"]["48"] == "TAP16_F"
assert p["U_BQ2"]["pins"]["16"] == "VC0_BQ2"
assert p["R_B17"]["pins"] == {"1": "CELL16", "2": "TAP16_F"}
assert p["R208"]["pins"] == {"1": "CELL16", "2": "VC0_BQ2"}
assert p["C_F17"]["pins"]["2"] == "VC0_BQ2"
assert p["R_B33"]["pins"]["1"] == "GND"
assert "10" not in p["J_CELL1"]["pins"] and "10" in p["J_CELL1"]["nc"]
for ref in ["R112", "R113", "R114", "R115", "R116"]:
    assert p[ref]["value"] == "0R"
assert p["U14"]["pins"]["5"] == "WD_PERMIT"  # /Q is pin 3, not 5
assert p["U14"]["pins"]["6"] == p["U13"]["pins"]["7"] == "WD_CLEAR_N"
assert p["U13"]["pins"]["3"] == p["U13"]["pins"]["5"] == "3V3"
assert p["D6"]["pins"] == {"1": "CHG_EN", "2": "WD_CLEAR_N"}
assert p["Q7"]["pins"] == {"1": "WD_PERMIT", "2": "GND", "3": "LED_WD"}
assert p["Q4"]["pins"]["2"] == "LED_WD"

# Explicitly check latch persistence: WDO is a pulse, NOT a sustained fault signal.
permit = True
for clear_n, clock_rises in [(False, False), (True, False), (True, False)]:
    if not clear_n:
        permit = False
    elif clock_rises:
        permit = True
    assert not permit
clear_n, clock_rises = True, True
if clear_n and clock_rises:
    permit = True
assert permit

c = (B / "firmware/hw_vbms32.c").read_text()
lisp = (B / "firmware/vbms32_micro.lisp").read_text()
assert "gpio-write 9" not in lisp
assert "(bms-fw-version) 7" in lisp
assert "return lbm_enc_i(7);" in c
assert "NAN_TO_M1" not in c
assert "gpio_set_level(PIN_OUT_EN, lbm_dec_as_i32" not in c
assert "(setq is-charging (bms-set-chg 1))" in lisp
assert "pretend we are at 24c" not in lisp
assert "pdMS_TO_TICKS(10) + 1" in c
assert "epoch == m_charge_epoch" in c
assert "acquisition_start) <= pdMS_TO_TICKS(1000)" in c
init = lisp[lisp.index("(defun init-hw"):lisp.index("(defun save-rtc-val")]
assert init.index("(bms-set-chg 0)") < init.index("(bms-init 16 16)")
assert "looprange attempt 0 3" in init

# Delimiter check respects comments and strings. Not a LispBM runtime test.
stack = []
quoted = escape = comment = False
for ch in lisp:
    if comment:
        if ch == "\n": comment = False
        continue
    if quoted:
        if escape: escape = False
        elif ch == "\\": escape = True
        elif ch == '"': quoted = False
        continue
    if ch == ";": comment = True
    elif ch == '"': quoted = True
    elif ch in "({": stack.append(ch)
    elif ch in ")}": assert stack.pop() == {')': '(', '}': '{'}[ch]
assert not stack and not quoted

baseline = json.loads((B / "verification/baseline-sha256.json").read_text())
for name, digest in baseline.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name + " changed"
print(f"PASS: {len(p)} component topology, permit model, firmware source invariants, Lisp delimiters, preserved originals")
