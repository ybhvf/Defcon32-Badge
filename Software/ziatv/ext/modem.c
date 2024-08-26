#include <stdbool.h>
#include <stddef.h>

#include "modem.h"

// Bandpass Filter
//////////////////
static const Q7_8 SOS[FILT_SECTIONS][6] = {
    {0.01188354, 0.02376707, 0.01188354, 1., -1.65975591, 0.8105545},
    {1., -2., 1., 1., -1.83076099, 0.88378139}};

static const filt_state_t filt_state_init = {
    .zi = {{0.30333257, -0.2436163}, {-0.31521611, 0.31521611}}};

static inline int16_t sos_filt(int16_t sample, filt_state_t *state) {
  // direct-form II iir filter
  Q7_8 *y_n = (Q7_8 *)&sample;
  for (uint16_t s = 0; s < FILT_SECTIONS; s++) {
    Q7_8 x_n = *y_n;
    *y_n = SOS[s][0] * x_n + state->zi[s][0];
    state->zi[s][0] = SOS[s][1] * x_n - SOS[s][4] * *y_n + state->zi[s][1];
    state->zi[s][1] = SOS[s][2] * x_n - SOS[s][5] * *y_n;
  }
  return sample;
}

// Zero-Crossing-Rate Frequency Discrimination
//////////////////////////////////////////////
static const zcr_state_t zcr_state_init = {.dt = 0, .last = 0};

static inline uint16_t zcr(int16_t sample, zcr_state_t *state) {
  if ((sample ^ state->last) < 0) {
    state->last = sample;
    uint16_t dt = state->dt;
    state->dt = 1;
    return dt;
  }
  state->dt++;
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
  dem->cur_freq = 0;
};

static void _dem_process(dem_t *dem) {
  // 1. Fill buffer
  dem->buf = dem->fill_func(dem->fill_arg);

  dem->T_len = 0;
  for (uint16_t i = 0; i < FRAMES; i++) {
    // 2. Bandpass filter on [1100hz, 2300hz]
    int16_t sample = sos_filt(dem->buf[i], &dem->filt_state);

    // 3. Demodulate
    sample = zcr(sample, &dem->zcr_state);

    if (sample > 0) {
      dem->buf[dem->T_len] = sample;
      dem->T_len++;
    }
  }
  dem->T_i = 0;
}

static void _dem_update(dem_t *dem) {
  if (dem->T_i >= dem->T_len) {
    _dem_process(dem);
  }

  dem->cur_ts = ((Q15_16)dem->buf[dem->T_i]) / SAMPLE_RATE;
  dem->cur_freq = 0.5 / dem->cur_ts;
}

uint16_t dem_read(dem_t *dem, Q15_16 length) {
  Q15_16 total = 0.0;
  Q15_16 rest = length;
  while (rest > dem->cur_ts) {
    rest -= dem->cur_ts;
    total += dem->cur_ts * dem->cur_freq;

    dem->T_i++;
    _dem_update(dem);
  }

  total += rest * dem->cur_freq;
  dem->cur_ts -= rest;

  return total / length;
}

static void _dem_fine_adjust(dem_t *dem, uint16_t freq) {
  uint16_t min_f = freq - FINE_HZ, max_f = freq + FINE_HZ;

  uint16_t heard = freq;
  while ((heard >= min_f) && (heard <= max_f)) {
    heard = dem_read(dem, FINE_S);
  }

  // TODO: something better
  dem->cur_ts += FINE_S / 2;
}

void dem_sync(dem_t *dem, uint16_t freq, Q15_16 length) {
  uint16_t min_f = freq - COARSE_HZ, max_f = freq + COARSE_HZ;

  // coarse adjustment
  Q15_16 step = length / (Q15_16)4;
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

void dem_expect(dem_t *dem, uint16_t freq, Q15_16 length) {
  uint16_t min_f = freq - COARSE_HZ, max_f = freq + COARSE_HZ;

  Q15_16 step = length / (Q15_16)2;

  // read half of tone
  uint16_t heard = dem_read(dem, step);
  if ((heard >= min_f) && (heard <= max_f)) {
    // if we're in the expected tone, do a fine adjustment
    _dem_fine_adjust(dem, freq);
  } else {
    // tone not found! continue free-running
    dem_read(dem, step);
  }
}

// Modulator (MODem)
//////////////////////

// TODO
