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

static void sos_filt(Q7_8 *chunk, filt_state_t *state) {
  // direct-form II iir filter
  for (uint16_t n = 0; n < FRAMES; n++) {
    Q7_8 y_n = chunk[n];
    for (uint16_t s = 0; s < FILT_SECTIONS; s++) {
      Q7_8 x_n = y_n;
      y_n = SOS[s][0] * x_n + state->zi[s][0];
      state->zi[s][0] = SOS[s][1] * x_n - SOS[s][4] * y_n + state->zi[s][1];
      state->zi[s][1] = SOS[s][2] * x_n - SOS[s][5] * y_n;
    }
    chunk[n] = y_n;
  }
}

// Zero-Crossing-Rate Frequency Discrimination
//////////////////////////////////////////////
static const zcr_state_t zcr_state_init = {.dt = 0, .last = 0};

static uint16_t zcr(int16_t *chunk, zcr_state_t *state) {
  uint16_t T_i = 0;
  for (uint16_t c_i = 0; c_i < FRAMES; c_i++) {
    if ((chunk[c_i] ^ state->last) < 0) {
      state->last = chunk[c_i];
      chunk[T_i] = state->dt;
      T_i++;
      state->dt = 0;
    }
    state->dt++;
  }
  return T_i;
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

  // 2. Bandpass filter on [1100hz, 2300hz]
  sos_filt((Q7_8 *)dem->buf, &dem->filt_state);

  // 3. Demodulate
  dem->T_len = zcr(dem->buf, &dem->zcr_state);
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
  Q15_16 step = length / 4.0;
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
  // read most of tone
  dem_read(dem, 0.8 * length);

  // fine adjustment
  _dem_fine_adjust(dem, freq);
}

// Modulator (MODem)
//////////////////////

// TODO
