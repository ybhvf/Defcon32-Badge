from lib.ili9341 import color565
from setup import display, rotary_enc, unispace


def menu_select(last_position, menu_items):
    # Force last_position to not equal rotary_enc.value() and be % = 0
    last_position = -len(menu_items)
    rotary_enc.reset()
    item_selected = False
    while item_selected is False:
        current_position = rotary_enc.value()

        # Generate a valid index from the position
        if current_position != last_position:
            index = current_position % len(menu_items)
            # Display item
            pretty_name = menu_items[index]["pretty"]
            text = str.format("{}: {}", index, pretty_name)
            display.draw_text(
                0,
                108,
                text,
                unispace,
                color565(0, 0, 0),
                background=color565(255, 255, 255),
            )
            last_position = current_position


def show_menu(menu, highlight, shift):
    """Shows the menu on the screen"""

    # menu variables
    item = 1
    line = 0
    line_height = 24
    offset = 5
    total_lines = 10

    # Shift the list of files so that it shows on the display
    short_list = []
    list_max = min(shift + total_lines, len(menu))
    for index in range(shift, list_max):
        try:
            short_list.append(menu[index]["pretty"])
        except IndexError:
            print("show_menu: Bad Index")
    for item in short_list:
        display.draw_text(
            0,
            line * line_height,
            "  " + item,
            unispace,
            color565(255, 255, 255),
            background=color565(0, 0, 0),
        )
        line += 1


def show_select(menu, highlight, shift):
    """Current selection icon"""

    # menu variables
    item = 1
    line = 0
    line_height = 24
    offset = 5
    total_lines = 10

    # Shift the list of files so that it shows on the display
    short_list = []
    list_max = min(shift + total_lines, len(menu))
    for index in range(shift, list_max):
        try:
            short_list.append(menu[index]["pretty"])
        except IndexError:
            print("show_menu: Bad Index")
    for item in short_list:
        if highlight == line:
            display.draw_text(
                0,
                line * line_height,
                ">",
                unispace,
                color565(255, 0, 0),
                background=color565(0, 0, 0),
            )
        else:
            display.draw_text(
                0,
                line * line_height,
                "  ",
                unispace,
                color565(255, 255, 255),
                background=color565(0, 0, 0),
            )
        line += 1
