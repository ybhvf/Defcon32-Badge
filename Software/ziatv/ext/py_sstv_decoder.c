#include <string.h>

#include "extmod/modmachine.h"
#include "py/obj.h"
#include "py/objarray.h"
#include "py/runtime.h"

#include "sstv.h"

#define printf(...) mp_printf(&mp_plat_print, __VA_ARGS__)

#define SCREEN_COLS 320
#define SCREEN_ROWS 240

void rgb_to_16bit(const uint8_t *r, const uint8_t *g, const uint8_t *b,
                  uint16_t len, uint16_t *c16) {
  for (unsigned y = 0; y < len; y++) {
    uint16_t color = (r[y] & 0xF8) << 8 | (g[y] & 0xFC) << 3 | b[y] >> 3;
    c16[y] = color >> 8 | color << 8;
  }
}

typedef struct {
  mp_obj_base_t base;
  mp_obj_t mic;
  mp_obj_t mic_readinto;

  mp_obj_t dem_buf_mv;

  dem_t dem;
  sstv_rx_t rx;

  uint16_t linebuf[SCREEN_COLS];
  mp_obj_t linebuf_mv;

  bool active;
  size_t cols;
  size_t rows;

  size_t row_idx;
  const char *msg;

  mp_obj_t display;
  mp_obj_t display_draw_text;
  mp_obj_t display_block;
  mp_obj_t unispace;
  mp_obj_t _thread_start_new_thread;

  mp_obj_t write_cb;
} sstv_Decoder_obj_t;

void _sstv_Decoder_fill_buf(sstv_Decoder_obj_t *self) {
  mp_call_function_2(self->mic_readinto, self->mic, self->dem_buf_mv);
}

void _sstv_Decoder_log(void *self_ptr, const char *str) {
  sstv_Decoder_obj_t *self = self_ptr;
  self->msg = str;
}

void _sstv_Decoder_setup(void *self_ptr, size_t cols, size_t rows) {
  sstv_Decoder_obj_t *self = self_ptr;
  self->cols = cols;
  self->rows = rows;
}

void _sstv_Decoder_draw(void *self_ptr, uint16_t x, const uint8_t *r,
                        const uint8_t *g, const uint8_t *b, size_t len) {
  sstv_Decoder_obj_t *self = self_ptr;
  rgb_to_16bit(r, g, b, self->cols, self->linebuf);
  self->row_idx = x;
}

// Rx.__init__(self)
mp_obj_t sstv_Decoder_make_new(const mp_obj_type_t *type, size_t n_args,
                               size_t n_kw, const mp_obj_t *args) {
  sstv_Decoder_obj_t *self = mp_obj_malloc(sstv_Decoder_obj_t, type);

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
           bits = MP_OBJ_NEW_SMALL_INT(16),
           rate = MP_OBJ_NEW_SMALL_INT(SAMPLE_RATE),
           ibuf = MP_OBJ_NEW_SMALL_INT(16000);

  mp_obj_t i2s_args[] = {MP_OBJ_NEW_SMALL_INT(1),
                         MP_OBJ_NEW_QSTR(MP_QSTR_sck), sck,
                         MP_OBJ_NEW_QSTR(MP_QSTR_ws), ws,
                         MP_OBJ_NEW_QSTR(MP_QSTR_sd), sd,
                         MP_OBJ_NEW_QSTR(MP_QSTR_mode), mode,
                         MP_OBJ_NEW_QSTR(MP_QSTR_format), fmt,
                         MP_OBJ_NEW_QSTR(MP_QSTR_bits), bits,
                         MP_OBJ_NEW_QSTR(MP_QSTR_rate), rate,
                         MP_OBJ_NEW_QSTR(MP_QSTR_ibuf), ibuf,
                         MP_OBJ_NULL};

  self->mic = MP_OBJ_TYPE_GET_SLOT(&machine_i2s_type, make_new)(&machine_i2s_type, 1, 8, i2s_args);
  // clang-format on

  mp_obj_t dest[2];
  mp_load_method(self->mic, MP_QSTR_readinto, dest);
  self->mic_readinto = dest[0];

  // Setup bytearray-backed buffer
  ////////////////////////////////
  self->dem_buf_mv =
      mp_obj_new_memoryview('b' | MP_OBJ_ARRAY_TYPECODE_FLAG_RW,
                            sizeof(self->dem.buf), self->dem.buf);
  self->linebuf_mv =
      mp_obj_new_memoryview('b' | MP_OBJ_ARRAY_TYPECODE_FLAG_RW,
                            sizeof(self->linebuf), self->linebuf);

  // Create demodulator
  /////////////////////
  dem_init(&self->dem, (dem_fill_func_t)_sstv_Decoder_fill_buf, self);

  // Setup receiver
  /////////////////
  self->rx.dem = &self->dem;

  self->rx._arg = self;

  self->rx.setup = _sstv_Decoder_setup;
  self->rx.log = _sstv_Decoder_log;
  self->rx.draw = _sstv_Decoder_draw;

  // Import display objects
  /////////////////////////

  // from setup import display, unispace
  mp_obj_t setup = mp_import_name(qstr_from_str("setup"), MP_OBJ_NULL, 0);
  self->display = mp_import_from(setup, qstr_from_str("display"));
  self->unispace = mp_import_from(setup, qstr_from_str("unispace"));

  mp_load_method(self->display, qstr_from_str("draw_text"), dest);
  self->display_draw_text = dest[0];
  mp_load_method(self->display, qstr_from_str("block"), dest);
  self->display_block = dest[0];

  mp_obj_t _thread = mp_import_name(qstr_from_str("_thread"), MP_OBJ_NULL, 0);
  mp_load_method(_thread, qstr_from_str("start_new_thread"), dest);
  self->_thread_start_new_thread = dest[0];

  self->write_cb = args[0];

  return MP_OBJ_FROM_PTR(self);
}

mp_obj_t sstv_Decoder__entry(mp_obj_t self_in) {
  sstv_Decoder_obj_t *self = MP_OBJ_TO_PTR(self_in);
  sstv_rx_decode(&self->rx);
  self->active = false;
  return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_1(sstv_Decoder__entry_obj, sstv_Decoder__entry);

mp_obj_t sstv_Decoder_run(mp_obj_t self_in) {
  sstv_Decoder_obj_t *self = MP_OBJ_TO_PTR(self_in);

  self->rows = 0;
  self->cols = 0;
  self->row_idx = 0;
  self->msg = NULL;
  self->active = true;

  mp_obj_t self_entry =
      mp_obj_new_bound_meth(MP_OBJ_FROM_PTR(&sstv_Decoder__entry_obj), self_in);
  mp_call_function_2(self->_thread_start_new_thread, self_entry,
                     MP_OBJ_FROM_PTR(&mp_const_empty_tuple_obj));

  // Update display
  size_t log_line = 0;
  while (self->active && self->rows == 0) {
    if (self->msg != NULL) {
      printf(self->msg);
      printf("\n");
      // display.draw_text(0, log_line, msg, unispace, 0xFFFF)
      mp_obj_t args[] = {self->display,
                         MP_OBJ_NEW_SMALL_INT(0),
                         MP_OBJ_NEW_SMALL_INT(log_line),
                         mp_obj_new_str(self->msg, strlen(self->msg)),
                         self->unispace,
                         MP_OBJ_NEW_SMALL_INT(0xFFFF),
                         MP_OBJ_NULL};
      mp_call_function_n_kw(self->display_draw_text, 6, 0, args);

      log_line += 24;
      self->msg = NULL;
    }
  }

  // Position the image so that the last row is drawn at the bottom of the
  // screen. Martin/Scottie modes include an optional 16-row header; this will
  // ensure that this header is drawn at the bottom, and then overwritten by the
  // image.
  size_t offset = ((2 * SCREEN_ROWS) - self->rows) % SCREEN_ROWS;

  size_t last_line = -1;
  do {
    size_t line = (offset + self->row_idx) % SCREEN_ROWS;
    if (line != last_line) {
      last_line = line;
      // display.block(0, line, SCREEN_COLS - 1, line, self.pixbuf)
      mp_obj_t args[] = {self->display,
                         MP_OBJ_NEW_SMALL_INT(0),
                         MP_OBJ_NEW_SMALL_INT(line),
                         MP_OBJ_NEW_SMALL_INT(SCREEN_COLS - 1),
                         MP_OBJ_NEW_SMALL_INT(line),
                         self->linebuf_mv,
                         MP_OBJ_NULL};
      mp_call_function_n_kw(self->display_block, 6, 0, args);
      // python callback for writing line to the sdcard
      mp_call_function_1(self->write_cb, self->linebuf_mv);
    }
  } while (self->active && self->row_idx < self->rows);

  return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_1(sstv_Decoder_run_obj, sstv_Decoder_run);

// Register locals (Rx.*)
const mp_rom_map_elem_t sstv_Decoder_locals_dict_table[] = {
    {MP_ROM_QSTR(MP_QSTR_run), MP_ROM_PTR(&sstv_Decoder_run_obj)},
    {MP_ROM_QSTR(MP_QSTR__entry), MP_ROM_PTR(&sstv_Decoder__entry_obj)},
};

MP_DEFINE_CONST_DICT(sstv_Decoder_locals_dict, sstv_Decoder_locals_dict_table);

// Register type(Rx)
MP_DEFINE_CONST_OBJ_TYPE(sstv_type_Decoder, MP_QSTR_Decoder, MP_TYPE_FLAG_NONE,
                         make_new, sstv_Decoder_make_new, locals_dict,
                         &sstv_Decoder_locals_dict);

// Register globals (sstv.*)
const mp_rom_map_elem_t sstv_globals_table[] = {
    {MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_sstv)},
    {MP_ROM_QSTR(MP_QSTR_Decoder), MP_ROM_PTR(&sstv_type_Decoder)},
};
MP_DEFINE_CONST_DICT(sstv_globals, sstv_globals_table);

// Register module
const mp_obj_module_t sstv_module = {
    .base = {&mp_type_module},
    .globals = (mp_obj_dict_t *)&sstv_globals,
};
MP_REGISTER_MODULE(MP_QSTR_sstv, sstv_module);
