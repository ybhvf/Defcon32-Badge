#include <stdint.h>
#include <sys/types.h>

#define SAMPLE_RATE 32000
#define FRAMES 4096

#define FINE_S 0.001
#define COARSE_HZ 20
#define FINE_HZ 100

#define FILT_SECTIONS 1

typedef void (*dem_fill_func_t)(void *farg);

typedef struct {
  float zi[FILT_SECTIONS][2];
} filt_state_t;

typedef struct {
  uint16_t dt;
  int16_t last;
} zcr_state_t;

typedef struct {
  dem_fill_func_t fill_func;
  void *fill_arg;

  int16_t buf[FRAMES];

  filt_state_t filt_state;
  zcr_state_t zcr_state;

  uint16_t T_len;
  uint16_t T_i;

  float cur_ts;
} dem_t;

void dem_init(dem_t *dem, dem_fill_func_t fptr, void *farg);
float dem_read(dem_t *dem, float dt);
void dem_sync(dem_t *dem, uint16_t freq, float dt);
void dem_expect(dem_t *dem, uint16_t freq, float dt);
