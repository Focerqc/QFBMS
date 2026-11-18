
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
static void charge_force_off(void) {
    portENTER_CRITICAL(&m_charge_mux);
    ++m_charge_epoch;
    gpio_set_level(PIN_CHG_EN, 0); // also asynchronously clears hardware permit
    gpio_set_level(PIN_PSW_EN, 0);
    gpio_set_level(PIN_OUT_EN, 0);
    m_charge_on = false;
    portEXIT_CRITICAL(&m_charge_mux);
}

static bool read_charge_snapshot(qfbms_snapshot *s) {
    *s = (qfbms_snapshot){.cell_min = 100.0f, .cell_max = -100.0f,
        .temp_min = 200.0f, .temp_max = -200.0f};
    main_config_t *cfg = (main_config_t *)&backup.config;
    if (m_cells_ic1 != 16 || m_cells_ic2 != 16 || cfg->temp_num < 1 || cfg->temp_num > 4) return false;
    bool ok = false;
    // A complete new acquisition is required on EVERY charge refresh. Neither
    // background telemetry nor a repeated old boolean can feed the watchdog.
    for (int chip = 0; chip < 2; chip++) {
        uint8_t addr = chip ? BQ_ADDR_2 : BQ_ADDR_1;
        int status = command_read(addr, ControlStatus, &ok);
        if (!ok || (status & 0x0004)) return false; // DEEPSLEEP: measurements stale
        for (int i = 0; i < 16; i++) {
            float v = command_read(addr, Cell1Voltage + 2 * i, &ok) / 1000.0f;
            if (!ok || v <= 0.0f || v > 5.0f) return false;
            s->cell_min = fminf(s->cell_min, v);
            s->cell_max = fmaxf(s->cell_max, v);
            s->cells++;
        }
    }
    const uint8_t registers[] = {TS1Temperature, TS3Temperature, ALERTTemperature, DCHGTemperature};
    for (int i = 0; i < cfg->temp_num; i++) {
        float voltage = command_read(BQ_ADDR_1, registers[i], &ok) * (0.358e-6f * 256.0f);
        float t;
        if (!ok || !qfbms_ntc(voltage, &t)) return false;
        s->temp_min = fminf(s->temp_min, t);
        s->temp_max = fmaxf(s->temp_max, t);
        s->sensors++;
    }
    float mos_v = command_read(BQ_ADDR_1, HDQTemperature, &ok) * (0.358e-6f * 256.0f);
    if (!ok || !qfbms_ntc(mos_v, &s->mos_temp)) return false;
    // PCB_VERSION 2 + 1mOhm: C current is 5x physical current. No CAN sum here.
    s->charge_amps = command_read(BQ_ADDR_1, CC2Current, &ok) / 500.0f;
    s->valid = ok;
    return ok;
}

static lbm_value ext_set_chg(lbm_value *args, lbm_uint argn) {
    LBM_CHECK_ARGN_NUMBER(1);
    if (!lbm_dec_as_i32(args[0])) {
        charge_force_off(); // no mutex, I2C or initialization can delay this
        return ENC_SYM_TRUE;
    }
    if (!m_lower_verified_10 || m_bq_init_active || !com_set_level(0)) {
        charge_force_off();
        return ENC_SYM_NIL;
    }
    xSemaphoreTake(bq_mutex, portMAX_DELAY);
    portENTER_CRITICAL(&m_charge_mux);
    unsigned epoch = m_charge_epoch;
    portEXIT_CRITICAL(&m_charge_mux);
    TickType_t acquisition_start = xTaskGetTickCount();
    qfbms_snapshot sample;
    main_config_t *cfg = (main_config_t *)&backup.config;
    qfbms_limits limits = {
        .cell_min = cfg->vc_charge_min,
        .cell_max = m_charge_on ? cfg->vc_charge_end : cfg->vc_charge_start,
        .temp_min = cfg->t_charge_min, .temp_max = cfg->t_charge_max,
        .mos_max = cfg->t_charge_max_mos,
        // 6A provisional ceiling for the selected 5A charger, pending bench validation.
        .current_max = fminf(cfg->max_charge_current, 6.0f)
    };
    bool allowed = isfinite(cfg->max_charge_current) && read_charge_snapshot(&sample) &&
        qfbms_charge_allowed(&sample, &limits) &&
        (xTaskGetTickCount() - acquisition_start) <= pdMS_TO_TICKS(1000);
    portENTER_CRITICAL(&m_charge_mux);
    allowed = allowed && epoch == m_charge_epoch;
    if (allowed) {
        gpio_set_level(PIN_PSW_EN, 1);
        gpio_set_level(PIN_CHG_EN, 1);
    }
    portEXIT_CRITICAL(&m_charge_mux);
    if (allowed) {
        // No lock held across scheduling; recheck the off epoch before each edge.
        vTaskDelay(1);
        portENTER_CRITICAL(&m_charge_mux);
        allowed = epoch == m_charge_epoch;
        if (allowed) gpio_set_level(PIN_OUT_EN, 1);
        portEXIT_CRITICAL(&m_charge_mux);
        vTaskDelay(1);
        portENTER_CRITICAL(&m_charge_mux);
        allowed = allowed && epoch == m_charge_epoch;
        gpio_set_level(PIN_OUT_EN, 0);
        if (allowed) m_charge_on = true;
        portEXIT_CRITICAL(&m_charge_mux);
    }
    if (!allowed) {
        charge_force_off();
        lbm_set_error_reason("Rev B charge inhibited: invalid, stale, or unsafe measurements");
    }
    xSemaphoreGive(bq_mutex);
    return allowed ? ENC_SYM_TRUE : ENC_SYM_NIL;
}
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
