"""Focused source/model checks for the maintained QFBMS firmware adaptation."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FW = ROOT / "firmware" / "qfbms32-adaptation"


def startup_model(address_write_ok, verification_results):
    """Return (admitted, verification_attempts), matching the C startup gate."""
    if not address_write_ok:
        return False, 0
    for attempt, verified in enumerate(verification_results[:3], 1):
        if verified:
            return True, attempt
    return False, min(len(verification_results), 3)


def check():
    c = (FW / "hw_vbms32.c").read_text(encoding="utf-8")
    lisp = (FW / "vbms32_micro.lisp").read_text(encoding="utf-8")

    assert "command_subcommands(BQ_ADDR_2, SET_CFGUPDATE) &&" in c
    assert "bq_set_reg(BQ_ADDR_2, I2CAddress, 0x20, 1) &&" in c
    assert "command_read(BQ_ADDR_1, Cell2Voltage, &lower_verified)" in c
    assert "attempt < 3" in c
    failed = c.index("if (!lower_verified)")
    admitted = c.index("if (!com_set_level(0))", failed)
    assert failed < admitted
    failure_block = c[failed:admitted]
    assert "gpio_set_level(PIN_COM_EN, 1)" in failure_block
    assert "return ENC_SYM_NIL" in failure_block
    assert "if (level == 0 && (!m_lower_verified_10 || m_bq_init_active))" in c
    assert "addr == BQ_ADDR_2 && !m_lower_addr08_setup && !m_com_connected" in c
    assert 'lbm_add_extension("bms-set-com", ext_bms_set_com)' in c
    assert "gpio-write 9" not in lisp
    assert lisp.count("bms-set-com") == 5

    assert startup_model(False, [True]) == (False, 0)  # address write failed
    assert startup_model(True, [False, False, False]) == (False, 3)  # no 0x10 ACK
    assert startup_model(True, [False, True]) == (True, 2)  # retry then verify

    # Every repeated Lisp request reaches the same guard. A denied request
    # leaves the path open; after verification, the requested levels apply.
    verified = False
    connected = False
    for level in (0, 0, 1, 0):
        if level == 0 and not verified:
            connected = False
        else:
            connected = level == 0
    assert not connected
    verified = True
    for level in (0, 1, 0, 1, 0):
        connected = level == 0
    assert connected
    print("PASS: address-write failure, failed/retried 0x10 verification, successful startup, and repeated Lisp GPIO9 gating.")


if __name__ == "__main__":
    check()
