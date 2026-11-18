/* QFBMS rev B: platform-independent safety policy, exercised by host C tests.
 * Derived from VBMS32's policy. This does not replace hardware qualification.
 */
#ifndef QFBMS_CHARGE_SAFETY_H
#define QFBMS_CHARGE_SAFETY_H
#include <stdbool.h>
#include <math.h>

typedef struct {
    float cell_min, cell_max, temp_min, temp_max, mos_temp, charge_amps;
    unsigned cells, sensors;
    bool valid;
} qfbms_snapshot;

typedef struct {
    float cell_min, cell_max, temp_min, temp_max, mos_max, current_max;
} qfbms_limits;

/* The hardware uses zero-ohm links, so only internal pad resistance is removed.
 * -300 is an invalid sentinel, never an acceptable operating temperature.
 * Nominal 18k/500R are inherited calibration assumptions, not precision claims.
 */
static inline bool qfbms_ntc(float volts, float *temperature) {
    *temperature = -300.0f;
    if (!isfinite(volts) || volts <= 0.0f || volts >= 1.8f) return false;
    float resistance = 18000.0f / (1.8f / volts - 1.0f) - 500.0f;
    if (!isfinite(resistance) || resistance < 100.0f || resistance > 500000.0f) return false;
    float t = 1.0f / (logf(resistance / 10000.0f) / 3380.0f + 1.0f / 298.15f) - 273.15f;
    if (!isfinite(t) || t < -40.0f || t > 125.0f) return false;
    *temperature = t;
    return true;
}

static inline bool qfbms_charge_allowed(const qfbms_snapshot *s, const qfbms_limits *l) {
    if (!s->valid || s->cells != 32 || s->sensors < 1 || s->sensors > 4) return false;
    if (!isfinite(s->cell_min) || !isfinite(s->cell_max) ||
        !isfinite(s->temp_min) || !isfinite(s->temp_max) ||
        !isfinite(s->mos_temp) || !isfinite(s->charge_amps)) return false;
    /* Comparisons written positively so NaN limits cannot grant permission. */
    return l->cell_min >= 2.0f && l->cell_max <= 4.21f && l->cell_min < l->cell_max &&
        l->temp_min >= 0.0f && l->temp_max <= 45.0f && l->temp_min < l->temp_max &&
        l->mos_max <= 85.0f && l->mos_max > 0.0f && l->current_max > 0.0f && l->current_max <= 6.0f &&
        s->cell_min > l->cell_min && s->cell_max < l->cell_max && s->cell_min <= s->cell_max &&
        s->temp_min > l->temp_min && s->temp_max < l->temp_max && s->temp_min <= s->temp_max &&
        s->mos_temp >= -40.0f && s->mos_temp < l->mos_max &&
        s->charge_amps >= -0.1f && s->charge_amps <= l->current_max;
}
#endif
