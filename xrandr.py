import pyrandr
import time


class XScreen:

    def __init__(self, pyrandr_screen):
        self._pyrandr_screen = pyrandr_screen

    @property
    def name(self):
        return self._pyrandr_screen.name

    @property
    def is_primary(self):
        return self._pyrandr_screen.primary

    @property
    def is_on(self):
        return self._is_enabled and self._is_connected

    @property
    def _is_enabled(self):
        return self._pyrandr_screen.is_enabled()

    @property
    def _is_connected(self):
        return self._pyrandr_screen.is_connected()


def get_enabled_x_screens():
    x_screens = map(XScreen, pyrandr.connected_screens())
    return [x_screen for x_screen in x_screens if x_screen.is_on]


def get_enabled_x_screens_and_poll_until_there_is_a_primary():
    while True:
        screens = get_enabled_x_screens()
        if not any(screen.is_primary for screen in screens):
            time.sleep(0.2)
        else:
            return screens
