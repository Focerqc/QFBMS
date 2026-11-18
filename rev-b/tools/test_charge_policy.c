#include <assert.h>
#include <stdio.h>
#include "../firmware/qfbms_charge_safety.h"

int main(void) {
    qfbms_snapshot good = {3.9f, 4.0f, 20, 25, 30, 5, 32, 1, true};
    qfbms_limits limits = {2, 4.16f, 0, 45, 85, 6};
    assert(qfbms_charge_allowed(&good, &limits));
    qfbms_snapshot s = good;
    s.valid = false; assert(!qfbms_charge_allowed(&s, &limits));
    s = good; s.cells = 16; assert(!qfbms_charge_allowed(&s, &limits));
    s = good; s.sensors = 0; assert(!qfbms_charge_allowed(&s, &limits));
    s = good; s.cell_max = 4.22f; assert(!qfbms_charge_allowed(&s, &limits));
    s = good; s.cell_min = 1.99f; assert(!qfbms_charge_allowed(&s, &limits));
    s = good; s.temp_min = -1; assert(!qfbms_charge_allowed(&s, &limits));
    s = good; s.temp_max = 46; assert(!qfbms_charge_allowed(&s, &limits));
    s = good; s.mos_temp = -300; assert(!qfbms_charge_allowed(&s, &limits));
    s = good; s.mos_temp = 86; assert(!qfbms_charge_allowed(&s, &limits));
    s = good; s.charge_amps = 6.01f; assert(!qfbms_charge_allowed(&s, &limits));
    s = good; s.charge_amps = -1; assert(!qfbms_charge_allowed(&s, &limits));
    s = good; s.cell_max = NAN; assert(!qfbms_charge_allowed(&s, &limits));
    s = good; s.mos_temp = INFINITY; assert(!qfbms_charge_allowed(&s, &limits));
    qfbms_limits bad = limits;
    bad.current_max = NAN; assert(!qfbms_charge_allowed(&good, &bad));
    bad = limits; bad.cell_max = 4.3f; assert(!qfbms_charge_allowed(&good, &bad));
    float t;
    assert(!qfbms_ntc(1.8f, &t) && t == -300); // open
    assert(!qfbms_ntc(1.8f * 500 / 18500, &t)); // short after internal pad
    assert(!qfbms_ntc(NAN, &t));
    assert(!qfbms_ntc(INFINITY, &t));
    for (int target = 0; target <= 85; target += 5) {
        float r = 10000.0f * expf(3380 * (1.0f / (target + 273.15f) - 1.0f / 298.15f));
        float v = 1.8f * (r + 500) / (18000 + r + 500);
        assert(qfbms_ntc(v, &t));
        assert(fabsf(t - target) < 0.01f);
    }
    puts("PASS: charge limits, missing data, sensor faults, non-finite values, 18 nominal NTC points");
    return 0;
}
