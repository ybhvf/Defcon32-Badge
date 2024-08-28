#include "extmod/modmachine.h"
#include "py/obj.h"
#include "py/runtime.h"

#include "modem.h"

#define debug_printf(...) mp_printf(&mp_plat_print, __VA_ARGS__)

typedef struct {
  mp_obj_base_t base;
  mp_obj_t mic;
  mp_obj_t mic_readinto;

  mp_obj_t buf_obj;
  int16_t *buf;

  dem_t dem;
} sstv_Dem_obj_t;

// Dem::process(self) -> void
int16_t *_sstv_Dem_fill_buf(sstv_Dem_obj_t *self) {
  mp_call_function_2(self->mic_readinto, self->mic, self->buf_obj);
  return self->buf;
}

// Dem.__init__(self)
static mp_obj_t sstv_Dem_make_new(const mp_obj_type_t *type) {
  sstv_Dem_obj_t *self = mp_obj_malloc(sstv_Dem_obj_t, type);

  // Create I2S mic for RX
  ////////////////////////
  // clang-format off
  mp_make_new_fun_t pin_init = MP_OBJ_TYPE_GET_SLOT(&machine_pin_type, make_new);
  mp_map_t *i2s_locals = &MP_OBJ_TYPE_GET_SLOT(&machine_i2s_type, locals_dict)->map;

  mp_obj_t sck = pin_init(&machine_pin_type, 1, 0, (mp_obj_t[]){MP_OBJ_NEW_SMALL_INT(0), MP_OBJ_NULL}),
           ws = pin_init(&machine_pin_type, 1, 0, (mp_obj_t[]){MP_OBJ_NEW_SMALL_INT(1), MP_OBJ_NULL}),
           sd = pin_init(&machine_pin_type, 1, 0, (mp_obj_t[]){MP_OBJ_NEW_SMALL_INT(3), MP_OBJ_NULL}),
           mode = mp_map_lookup(i2s_locals, MP_OBJ_NEW_QSTR(MP_QSTR_RX), MP_MAP_LOOKUP)->value,
           fmt = mp_map_lookup(i2s_locals, MP_OBJ_NEW_QSTR(MP_QSTR_MONO), MP_MAP_LOOKUP) ->value,
           bits = MP_OBJ_NEW_SMALL_INT(16), rate = MP_OBJ_NEW_SMALL_INT(32000),
           ibuf = MP_OBJ_NEW_SMALL_INT(SAMPLE_RATE);

  mp_obj_t args[] = {MP_OBJ_NEW_SMALL_INT(1),
                     MP_OBJ_NEW_QSTR(MP_QSTR_sck), sck,
                     MP_OBJ_NEW_QSTR(MP_QSTR_ws), ws,
                     MP_OBJ_NEW_QSTR(MP_QSTR_sd), sd,
                     MP_OBJ_NEW_QSTR(MP_QSTR_mode), mode,
                     MP_OBJ_NEW_QSTR(MP_QSTR_format), fmt,
                     MP_OBJ_NEW_QSTR(MP_QSTR_bits), bits,
                     MP_OBJ_NEW_QSTR(MP_QSTR_rate), rate,
                     MP_OBJ_NEW_QSTR(MP_QSTR_ibuf), ibuf,
                     MP_OBJ_NULL};

  self->mic = MP_OBJ_TYPE_GET_SLOT(&machine_i2s_type, make_new)(&machine_i2s_type, 1, 8, args);
  // clang-format on

  mp_obj_t dest[2];
  mp_load_method(self->mic, MP_QSTR_readinto, dest);
  self->mic_readinto = dest[0];

  // Setup bytearray-backed buffer
  ////////////////////////////////
  self->buf_obj = mp_obj_new_bytearray(FRAMES * sizeof(int16_t), NULL);
  mp_buffer_info_t buf_info;
  mp_get_buffer(self->buf_obj, &buf_info, MP_BUFFER_RW);
  self->buf = (int16_t *)buf_info.buf;

  // Create demodulator
  /////////////////////
  dem_init(&self->dem, (dem_fill_func_t)_sstv_Dem_fill_buf, self);

  return MP_OBJ_FROM_PTR(self);
}

static mp_obj_t sstv_Dem_read(mp_obj_t self_in, mp_obj_t length_obj) {
  sstv_Dem_obj_t *self = MP_OBJ_TO_PTR(self_in);
  uint16_t freq = dem_read(&self->dem, mp_obj_get_float(length_obj));
  return mp_obj_new_int(freq);
}

static mp_obj_t sstv_Dem_expect(mp_obj_t self_in, mp_obj_t freq_obj,
                                mp_obj_t length_obj) {
  sstv_Dem_obj_t *self = MP_OBJ_TO_PTR(self_in);
  dem_expect(&self->dem, mp_obj_get_int(freq_obj),
             mp_obj_get_float(length_obj));
  return mp_const_none;
}

static mp_obj_t sstv_Dem_sync(mp_obj_t self_in, mp_obj_t freq_obj,
                              mp_obj_t length_obj) {
  sstv_Dem_obj_t *self = MP_OBJ_TO_PTR(self_in);
  dem_sync(&self->dem, mp_obj_get_int(freq_obj), mp_obj_get_float(length_obj));
  return mp_const_none;
}

static inline uint8_t _decode_color(uint16_t freq) {
  const Q15_16 f_step = 3.1372549;

  if (freq < 1500) {
    freq = 1500;
  } else if (freq > 2300) {
    freq = 2300;
  }

  freq -= 1500;
  return ((Q15_16)freq) / f_step;
}

static mp_obj_t sstv_Dem_read_line(mp_obj_t self_in, mp_obj_t buf_obj,
                                   mp_obj_t length_obj) {
  sstv_Dem_obj_t *self = MP_OBJ_TO_PTR(self_in);
  Q15_16 length = mp_obj_get_float(length_obj);

  mp_buffer_info_t buf_info;
  mp_get_buffer(buf_obj, &buf_info, MP_BUFFER_WRITE);
  uint8_t *buf = (uint8_t *)buf_info.buf;

  for (uint16_t i = 0; i < buf_info.len; i++) {
    uint16_t freq = dem_read(&self->dem, length);
    buf[i] = _decode_color(freq);
  }

  return mp_const_none;
}

// Register locals (Dem.*)
static MP_DEFINE_CONST_FUN_OBJ_2(sstv_Dem_read_obj, sstv_Dem_read);
static MP_DEFINE_CONST_FUN_OBJ_3(sstv_Dem_sync_obj, sstv_Dem_sync);
static MP_DEFINE_CONST_FUN_OBJ_3(sstv_Dem_expect_obj, sstv_Dem_expect);
static MP_DEFINE_CONST_FUN_OBJ_3(sstv_Dem_read_line_obj, sstv_Dem_read_line);

static const mp_rom_map_elem_t sstv_Dem_locals_dict_table[] = {
    {MP_ROM_QSTR(MP_QSTR_read), MP_ROM_PTR(&sstv_Dem_read_obj)},
    {MP_ROM_QSTR(MP_QSTR_sync), MP_ROM_PTR(&sstv_Dem_sync_obj)},
    {MP_ROM_QSTR(MP_QSTR_expect), MP_ROM_PTR(&sstv_Dem_expect_obj)},
    {MP_ROM_QSTR(MP_QSTR_read_line), MP_ROM_PTR(&sstv_Dem_read_line_obj)},
};

static MP_DEFINE_CONST_DICT(sstv_Dem_locals_dict, sstv_Dem_locals_dict_table);

// Register type(Dem)
MP_DEFINE_CONST_OBJ_TYPE(sstv_type_Dem, MP_QSTR_Dem, MP_TYPE_FLAG_NONE,
                         make_new, sstv_Dem_make_new, locals_dict,
                         &sstv_Dem_locals_dict);

// Register globals (sstv.*)
static const mp_rom_map_elem_t sstv_globals_table[] = {
    {MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_sstv)},
    {MP_ROM_QSTR(MP_QSTR_Dem), MP_ROM_PTR(&sstv_type_Dem)},
};
static MP_DEFINE_CONST_DICT(sstv_globals, sstv_globals_table);

// Register module
const mp_obj_module_t sstv_module = {
    .base = {&mp_type_module},
    .globals = (mp_obj_dict_t *)&sstv_globals,
};
MP_REGISTER_MODULE(MP_QSTR_sstv, sstv_module);
