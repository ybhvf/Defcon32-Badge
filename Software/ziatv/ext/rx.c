#include "sstv.h"

uint8_t decode_color(uint16_t freq) {
  const float f_step = 3.1372549;

  if (freq < 1500) {
    freq = 1500;
  } else if (freq > 2300) {
    freq = 2300;
  }

  freq -= 1500;
  return ((float)freq) / f_step;
}

void read_line(dem_t *dem, uint8_t *buf, size_t buf_len, float pix_dt) {
  for (size_t i = 0; i < buf_len; i++) {
    uint16_t freq = dem_read(dem, pix_dt);
    buf[i] = decode_color(freq);
  }
}

void read_scottie(sstv_rx_t *self, uint16_t cols, uint16_t rows, float pix_dt) {
  uint8_t red[cols], green[cols], blue[cols];
  self->setup(self->_arg, cols, rows);

  dem_expect(self->dem, 1200, 0.009); // SYNC @ 1200hz

  for (size_t x = 0; x < rows; x++) {
    // green
    dem_read(self->dem, 0.0015); // 1500hz ref
    read_line(self->dem, green, cols, pix_dt);

    // blue
    dem_read(self->dem, 0.0015); // 1500hz ref
    read_line(self->dem, blue, cols, pix_dt);
    dem_expect(self->dem, 1200, 0.009); // SYNC @ 1200hz

    // red
    dem_read(self->dem, 0.0015); // 1500hz ref
    read_line(self->dem, red, cols, pix_dt);

    self->draw(self->_arg, x, red, green, blue, cols);
  }
}

void read_martin(sstv_rx_t *self, uint16_t cols, uint16_t rows, float pix_dt) {
  uint8_t red[cols], green[cols], blue[cols];
  self->setup(self->_arg, cols, rows);

  for (size_t x = 0; x < rows; x++) {
    dem_expect(self->dem, 1200, 0.004862); // SYNC @ 1200hz
    dem_read(self->dem, 0.000572); // 1500hz ref

    // green
    read_line(self->dem, green, cols, pix_dt);
    dem_read(self->dem, 0.000572); // 1500hz ref

    // blue
    read_line(self->dem, blue, cols, pix_dt);
    dem_read(self->dem, 0.000572); // 1500hz ref

    // red
    read_line(self->dem, red, cols, pix_dt);
    dem_read(self->dem, 0.000572); // 1500hz ref

    self->draw(self->_arg, x, red, green, blue, cols);
  }
}

void sstv_rx_decode(sstv_rx_t *self) {
  self->log(self->_arg, "listening for sstv");

  // read calibration header
  dem_sync(self->dem, 1900, 0.3);
  dem_read(self->dem, 0.01); // 1200hz
  dem_read(self->dem, 0.3);  // 1900hz

  self->log(self->_arg, "heard calibration header");

  // read VIS code
  dem_read(self->dem, 0.03); // start bit (1200hz)
  uint8_t vis = 0;
  for (uint8_t idx = 0; idx < 7; idx++) {
    uint8_t bit = dem_read(self->dem, 0.03) <= 1200;
    vis |= bit << idx;
  }
  uint8_t parity =
      dem_read(self->dem, 0.03) <= 1200; // ignore parity bit for the moment
  parity = parity;

  dem_read(self->dem, 0.03); // stop bit (1200hz)

  // SCOTTIE MODES
  if (vis == 60) {
    self->log(self->_arg, "decoding scottie 1");
    read_scottie(self, 320, 256, 0.0004320);
  } else if (vis == 56) {
    self->log(self->_arg, "decoding scottie 2");
    read_scottie(self, 320, 256, 0.0002752);
  } else if (vis == 52) {
    self->log(self->_arg, "decoding scottie 3");
    read_scottie(self, 320, 128, 0.0004320);
  } else if (vis == 48) {
    self->log(self->_arg, "decoding scottie 4");
    read_scottie(self, 320, 128, 0.0002752);
    // MARTIN MODES
  } else if (vis == 44) {
    self->log(self->_arg, "decoding martin 1");
    read_martin(self, 320, 256, 0.0004576);
  } else if (vis == 40) {
    self->log(self->_arg, "decoding martin 2");
    read_martin(self, 320, 256, 0.0002288);
  } else if (vis == 36) {
    self->log(self->_arg, "decoding martin 3");
    read_martin(self, 320, 128, 0.0004576);
  } else if (vis == 32) {
    self->log(self->_arg, "decoding martin 4");
    read_martin(self, 320, 128, 0.0002288);
    // FAILURE
  } else {
    self->log(self->_arg, "unknown vis");
    self->log(self->_arg, "decode failed!");
  }
}
