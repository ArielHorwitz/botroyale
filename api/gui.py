from collections import namedtuple


"""
VFX arguments:
name        Name of image (without .png extension)
hex         Hex on which to center the image
neighbor    Neighbor Hex for image rotation
time        How many in-game steps to show the image
real_time   How many real-time seconds to show the image
"""
VFX = namedtuple('VFX', ['name', 'hex', 'neighbor', 'time', 'real_time'])
TileGUI = namedtuple('TileGUI', ['bg_color', 'bg_text', 'fg_color', 'fg_text', 'fg_sprite'])
GuiControlMenu = namedtuple('GuiControlMenu', ['label', 'controls'])
GuiControl = namedtuple('GuiControl', ['label', 'callback', 'hotkey'])


def gui_control_menu_extend(menu1, menu2):
    """Extend a GuiControlMenu with elements from another GuiControlMenu."""
    for submenu2 in menu2:
        # Find matching submenu
        for submenu1 in menu1:
            if submenu2.label == submenu1.label:
                submenu1.controls.extend(submenu2.controls)
                break
        else:
            menu1.append(submenu2)
