"""Compile the ACTUAL new C charge functions against fault-injecting host stubs.

This verifies these functions, not ESP-IDF integration, ADC hardware, or LispBM.
"""
from pathlib import Path
import os
import subprocess

B = Path(__file__).resolve().parents[1]
src = (B / "firmware/hw_vbms32.c").read_text()

def function(signature):
    start = src.index(signature)
    opening = src.index("{", start)
    depth = 1
    i = opening + 1
    while depth:
        depth += (src[i] == "{") - (src[i] == "}")
        i += 1
    return src[start:i]

prelude = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "../firmware/qfbms_charge_safety.h"
#include "../../_reference/firmware/bq769x2_defs.h"
#define BQ_ADDR_1 0x10
#define BQ_ADDR_2 0x08
#define PIN_CHG_EN 5
#define PIN_PSW_EN 10
#define PIN_OUT_EN 4
#define portMAX_DELAY 0
#define portENTER_CRITICAL(x) ((void)(x))
#define portEXIT_CRITICAL(x) ((void)(x))
#define pdMS_TO_TICKS(x) (x)
#define ENC_SYM_TRUE 1
#define ENC_SYM_NIL 0
#define LBM_CHECK_ARGN_NUMBER(x) ((void)argn)
typedef int lbm_value;
typedef unsigned lbm_uint;
typedef unsigned TickType_t;
typedef struct {
    int temp_num;
    float vc_charge_min, vc_charge_start, vc_charge_end;
    float t_charge_min, t_charge_max, t_charge_max_mos, max_charge_current;
} main_config_t;
static struct { main_config_t config; } backup;
static int m_cells_ic1 = 16, m_cells_ic2 = 16;
static bool m_charge_on, m_lower_verified_10 = true, m_bq_init_active;
static int bq_mutex, m_charge_mux;
static unsigned m_charge_epoch;
static int pins[32], edges, reads, fail_read, off_at_read, off_at_delay, delays;
static unsigned ticks, read_delay;
static int raw_current = 2500; // +25A C => +5A physical charging
static int bad_sensor, status_value;
static void charge_force_off(void);
static void gpio_set_level(int p, int v) { pins[p] = v; if (p == 4 && v) edges++; }
static void xSemaphoreTake(int m, int t) { (void)m; (void)t; }
static void xSemaphoreGive(int m) { (void)m; }
static unsigned xTaskGetTickCount(void) { return ticks; }
static void vTaskDelay(int t) { ticks += t; if (++delays == off_at_delay) charge_force_off(); }
static int lbm_dec_as_i32(int a) { return a; }
static void lbm_set_error_reason(const char *s) { (void)s; }
static bool com_set_level(int l) { (void)l; return true; }
static int16_t command_read(uint8_t a, uint8_t r, bool *ok) {
    (void)a; ++reads; ticks += read_delay;
    if (reads == off_at_read) charge_force_off();
    *ok = reads != fail_read;
    if (!*ok) return -1;
    if (r == ControlStatus) return status_value;
    if (r >= Cell1Voltage && r <= Cell16Voltage) return 4000;
    if (r == CC2Current) return raw_current;
    if (r == HDQTemperature && bad_sensor) return 19640; // open, approximately REG18
    return (int16_t)((1.8 * 10500 / 28500) / (0.358e-6 * 256));
}
'''
body = "\n\n".join(function(s) for s in [
    "static void charge_force_off(", "static bool read_charge_snapshot(",
    "static lbm_value ext_set_chg("])
tests = r'''
static void reset(void) {
    backup.config = (main_config_t){1, 2, 4.16f, 4.21f, 0, 45, 85, 6};
    charge_force_off();
    edges = reads = delays = fail_read = off_at_read = off_at_delay = 0;
    ticks = read_delay = 0; raw_current = 2500; bad_sensor = status_value = 0;
    m_lower_verified_10 = true; m_bq_init_active = false;
}
static int request(int on) { lbm_value a = on; return ext_set_chg(&a, 1); }
static void assert_off(void) { assert(!pins[5] && !pins[10] && !pins[4] && !m_charge_on); }
int main(void) {
    reset(); assert(request(1)); assert(pins[5] && pins[10] && edges == 1);
    int acquisition_reads = reads;
    assert(request(1)); assert(reads == 2 * acquisition_reads); // cannot reuse old data
    assert(request(0)); assert_off();
    for (int i = 1; i <= acquisition_reads; i++) {
        reset(); m_charge_on = true; pins[5] = pins[10] = 1; fail_read = i;
        assert(!request(1)); assert_off(); assert(edges == 0);
    }
    reset(); bad_sensor = 1; assert(!request(1)); assert_off();
    reset(); raw_current = 3500; assert(!request(1)); assert_off();
    reset(); raw_current = -2500; assert(!request(1)); assert_off();
    reset(); status_value = 4; assert(!request(1)); assert_off();
    reset(); backup.config.temp_num = 0; assert(!request(1)); assert_off();
    reset(); backup.config.max_charge_current = NAN; assert(!request(1)); assert_off();
    reset(); read_delay = 50; assert(!request(1)); assert_off();
    reset(); m_lower_verified_10 = false; assert(!request(1)); assert_off();
    reset(); m_bq_init_active = true; assert(!request(1)); assert_off();
    reset(); off_at_read = 12; assert(!request(1)); assert_off(); assert(edges == 0);
    reset(); off_at_delay = 1; assert(!request(1)); assert_off(); assert(edges == 0);
    reset(); off_at_delay = 2; assert(!request(1)); assert_off();
    reset(); fail_read = 1; assert(request(0)); assert(reads == 0); assert_off();
    printf("PASS: actual C charge path, %d individual read faults, repeated acquisition, timeout, reset, sensor/current faults, concurrent OFF\n", acquisition_reads);
}
'''
out = B / "verification/charge_integration.c"
out.write_text(prelude + body + tests)
gcc = os.environ.get("CC", r"C:\devkitPro\msys2\mingw64\bin\gcc.exe")
env = dict(os.environ)
env["PATH"] = str(Path(gcc).parent) + os.pathsep + env["PATH"]
exe = out.with_suffix(".exe")
subprocess.run([gcc, "-std=c11", "-Wall", "-Wextra", "-Werror", str(out), "-o", str(exe)], check=True, env=env)
subprocess.run([str(exe)], check=True, env=env)
