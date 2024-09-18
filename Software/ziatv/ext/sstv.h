#include "modem.h"

#include "py/runtime.h"
#define printf(...) mp_printf(&mp_plat_print, __VA_ARGS__)

typedef struct {
  dem_t *dem;

  void (*log)(void *, const char *str);
  void (*setup)(void *, size_t cols, size_t rows);
  void (*draw)(void *, uint16_t x, const uint8_t *r, const uint8_t *g,
               const uint8_t *b, size_t len);
  void *_arg;

} sstv_rx_t;

void sstv_rx_decode(sstv_rx_t *self);

typedef struct {
} sstv_tx_t;
