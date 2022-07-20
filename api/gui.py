from collections import namedtuple


"""
VFX arguments:
name            Name of image (without .png extension)
hex             Hex on which to center the image
direction       Direction hex for image rotation
start_step      The in-game step which marks the start of the visual effect
expire_step     The in-game step which marks the end of the visual effect
expire_seconds  Real-time seconds after which the visual effect is over
"""
VFX = namedtuple('VFX', ['name', 'hex', 'direction', 'start_step', 'expire_step', 'expire_seconds'])
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
