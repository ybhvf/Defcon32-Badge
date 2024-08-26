#include <stdint.h>

#define SAMPLE_RATE 32000
#define FRAMES 4096

#define FINE_S 0.001
#define COARSE_HZ 10
#define FINE_HZ 50

#define FILT_SECTIONS 2

typedef _Accum long Q15_16;
typedef _Accum short Q7_8;

typedef int16_t *(*dem_fill_func_t)(void *farg);

typedef struct {
  Q7_8 zi[FILT_SECTIONS][2];
} filt_state_t;

typedef struct {
  uint16_t dt;
  int16_t last;
} zcr_state_t;

typedef struct {
  dem_fill_func_t fill_func;
  void *fill_arg;

  int16_t *buf;

  filt_state_t filt_state;
  zcr_state_t zcr_state;

  uint16_t T_len;
  uint16_t T_i;

  Q15_16 cur_freq;
  Q15_16 cur_ts;
} dem_t;

void dem_init(dem_t *dem, dem_fill_func_t fptr, void *farg);
uint16_t dem_read(dem_t *dem, Q15_16 length);
void dem_sync(dem_t *dem, uint16_t freq, Q15_16 length);
void dem_expect(dem_t *dem, uint16_t freq, Q15_16 length);
