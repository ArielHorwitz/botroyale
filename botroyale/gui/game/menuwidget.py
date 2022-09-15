"""An interactive widget for the game's main menu."""
from botroyale.gui.kex import widgets
from botroyale.api.gui import InputWidget
from botroyale.api.gui import PALETTE_BG
from botroyale.util import settings


MENU_WIDGET_SIZE = settings.get('gui.menu.widget_size')


class MenuWidget(widgets.AnchorLayout):
    def __init__(self, iw: InputWidget, **kwargs):
        super().__init__(**kwargs)
        assert isinstance(iw, InputWidget)
        self.type = iw.type
        self.label = iw.label
        self.default = iw.default
        self.sendto = iw.sendto
        self.options = iw.options
        self.get_value = None
        self.set_size(*MENU_WIDGET_SIZE)
        self.container = self.add(widgets.BoxLayout(orientation='vertical'))
        self.container.set_size(hx=0.95, hy=0.9)

    def double_height(self, multi=2):
        self.set_size(x=MENU_WIDGET_SIZE[0], y=MENU_WIDGET_SIZE[1]*multi)


class Spacer(MenuWidget):
    def __init__(self, iw, **kwargs):
        super().__init__(iw, **kwargs)
        self.remove_widget(self.container)
        self.anchor_y = 'bottom'
        label = self.add(widgets.MLabel(text=iw.label))
        label.make_bg(PALETTE_BG[0])
        if self.type != 'divider':
            self.double_height(multi=2)
            label.set_size(hy=0.75)
        else:
            self.double_height(multi=1.5)


class Toggle(MenuWidget):
    def __init__(self, iw, **kwargs):
        super().__init__(iw, **kwargs)
        btn = self.container.add(widgets.ToggleButton(text=iw.label))
        btn.active = iw.default
        self.get_value = lambda: btn.active


class Text(MenuWidget):
    def __init__(self, iw, **kwargs):
        super().__init__(iw, **kwargs)
        self.double_height()
        label = self.container.add(widgets.MLabel(text=iw.label))
        entry = self.container.add(widgets.Entry(text=iw.default))
        self.get_value = lambda: entry.text


class Select(MenuWidget):
    def __init__(self, iw, **kwargs):
        super().__init__(iw, **kwargs)
        self.double_height()
        if iw.options is None:
            raise ValueError(f'Cannot make a select InputWidget without options')
        label = self.container.add(widgets.MLabel(text=iw.label))
        dropdown = self.container.add(widgets.DropDownSelect(callback=lambda *a: None))
        dropdown.text = iw.default
        dropdown.set_options(iw.options)
        self.get_value = lambda: dropdown.text


# The class name "Slider" confuses kivy
class Slider_(MenuWidget):
    def __init__(self, iw, **kwargs):
        super().__init__(iw, **kwargs)
        self.double_height()
        label = self.container.add(widgets.MLabel(text=iw.label))
        slider = self.container.add(widgets.Slider())
        slider.value = iw.default
        self.get_value = lambda: slider.value


def get_menu_widget(iw):
    if iw.type == 'spacer' or iw.type == 'divider':
        return Spacer(iw)
    elif iw.type == 'toggle':
        return Toggle(iw)
    elif iw.type == 'text':
        return Text(iw)
    elif iw.type == 'select':
        return Select(iw)
    elif iw.type == 'slider':
        return Slider_(iw)
    else:
        raise ValueError(f'Unknown InputWidget type: {iw.type}')
