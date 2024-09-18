#include <stdbool.h>
#include <stddef.h>

#include "py/runtime.h"
#define printf(...) mp_printf(&mp_plat_print, __VA_ARGS__)

#include "modem.h"

// Bandpass Filter
//////////////////
static const float SOS[FILT_SECTIONS][6] = {
    {0.10583178, 0., -0.10583178, 1., -1.70142457, 0.78833643}};

const filt_state_t filt_state_init = {.zi = {{0., 0.}}};

int16_t sos_filt(int16_t sample, filt_state_t *state) {
  // direct-form II iir filter
  float y_n = sample;
  for (size_t s = 0; s < FILT_SECTIONS; s++) {
    float x_n = y_n;
    y_n = SOS[s][0] * x_n + state->zi[s][0];
    state->zi[s][0] = SOS[s][1] * x_n - SOS[s][4] * y_n + state->zi[s][1];
    state->zi[s][1] = SOS[s][2] * x_n - SOS[s][5] * y_n;
  }
  return y_n;
}

// Zero-Crossing-Rate Frequency Discrimination
//////////////////////////////////////////////
const zcr_state_t zcr_state_init = {.dt = 0, .last = 0};

uint16_t zcr(int16_t sample, zcr_state_t *state) {
  state->dt++;
  if ((sample ^ state->last) < 0) {
    state->last = sample;
    uint16_t dt = state->dt;
    state->dt = 0;
    return dt;
  }
  return 0;
}

// Demodulator (moDEM)
//////////////////////
void dem_init(dem_t *dem, dem_fill_func_t fptr, void *farg) {
  dem->fill_func = fptr;
  dem->fill_arg = farg;

  dem->filt_state = filt_state_init;
  dem->zcr_state = zcr_state_init;

  dem->T_i = 0;
  dem->T_len = 0;

  dem->cur_ts = 0;
};

void _dem_process(dem_t *dem) {
  // 1. Fill buffer
  dem->fill_func(dem->fill_arg);

  dem->T_len = 0;
  for (size_t i = 0; i < FRAMES; i++) {
    // 2. Bandpass filter on [1100hz, 2300hz]
    int16_t sample = sos_filt(dem->buf[i], &dem->filt_state);
    // int16_t sample = dem->buf[i];

    // 3. Demodulate
    sample = zcr(sample, &dem->zcr_state);

    if (sample > 0) {
      dem->buf[dem->T_len] = sample;
      dem->T_len++;
    }
  }
  dem->T_i = 0;
}

void _dem_update(dem_t *dem) {
  if (dem->T_i >= dem->T_len) {
    _dem_process(dem);
  }

  dem->cur_ts = dem->buf[dem->T_i];
}

float dem_read(dem_t *dem, float dt) {
  float samples = dt * SAMPLE_RATE;

  float rest = samples;
  float total = 0;
  while (rest > dem->cur_ts) {
    rest -= dem->cur_ts;
    total += dem->cur_ts * dem->buf[dem->T_i];

    dem->T_i++;
    _dem_update(dem);
  }

  total += rest * dem->buf[dem->T_i];
  dem->cur_ts -= rest;

  total /= samples;

  return (float)SAMPLE_RATE / total / 2.0;
}

void _dem_fine_adjust(dem_t *dem, uint16_t freq) {
  uint16_t min_f = freq - FINE_HZ, max_f = freq + FINE_HZ;

  uint16_t heard = freq;
  while ((heard >= min_f) && (heard <= max_f)) {
    heard = dem_read(dem, FINE_S);
  }

  // TODO: something better
  dem->cur_ts += FINE_S * SAMPLE_RATE / 2.0;
}

void dem_sync(dem_t *dem, uint16_t freq, float dt) {
  uint16_t min_f = freq - COARSE_HZ, max_f = freq + COARSE_HZ;

  // coarse adjustment
  float step = dt / 4.0;
  uint16_t count = 0;
  while (count < 3) {
    uint16_t heard = dem_read(dem, step);
    if ((heard >= min_f) && (heard <= max_f)) {
      count += 1;
    } else {
      count = 0;
    }
  }

  // fine adjustment
  _dem_fine_adjust(dem, freq);
}

void dem_expect(dem_t *dem, uint16_t freq, float dt) {
  uint16_t min_f = freq - COARSE_HZ, max_f = freq + COARSE_HZ;

  float step = 0.98 * dt;

  // read half of tone
  uint16_t heard = dem_read(dem, step);
  if ((heard >= min_f) && (heard <= max_f)) {
    // if we're in the expected tone, do a fine adjustment
    _dem_fine_adjust(dem, freq);
  } else {
    // tone not found! continue free-running
    dem_read(dem, dt - step);
  }
}

// Modulator (MODem)
//////////////////////

// TODO
