#!/usr/bin/env python3

import time

import pyudev
from bspwm import Bspwm
from xrandr import get_enabled_x_screens_and_poll_until_there_is_a_primary

padding_for_primary = 42

desktop_layouts = [
    # used for whichever screen is the primary
    '1 2 3 4 5 6 7'.split(),
    # used for the second plugged in screen
    'I II II IV'.split(),
    # used for the third plugged in screen, more rare
    'a b c d'.split(),
    # used for the fourth plugged in screen, extremely rare
    'A B C D'.split(),
    # used for the fifth plugged in screen, if you have more screens than this
    # i'm going to crash the program
    '一 二 三 四 語'.split(),
]


def on_monitor_change():
    bspwm_monitors = Bspwm.monitors()
    print(f'all bspwm monitors: {repr(bspwm_monitors)}')
    enabled_x_screens = get_enabled_x_screens_and_poll_until_there_is_a_primary()
    print(f'enabled x screens: {repr(enabled_x_screens)}')

    enabled_screen_names = [screen.name for screen in enabled_x_screens]
    bspwm_monitors_to_be_turned_off = [s for s in bspwm_monitors if s.name not in
                                     enabled_screen_names]

    active_bspwm_monitors = [m for m in bspwm_monitors if m not in bspwm_monitors_to_be_turned_off]

    print('bspwm_monitors_to_be_turned_off', repr(bspwm_monitors_to_be_turned_off))
    print('active_bspwm_monitors', repr(active_bspwm_monitors))

    [primary_screen] = [s for s in enabled_x_screens if s.is_primary]
    # move the primary desktop to the first spot in the list, the first desktop
    # layout is meant for it.
    [primary_monitor_index] = [i for i, m in enumerate(active_bspwm_monitors) if
                               m.name == primary_screen.name]
    active_bspwm_monitors.insert(0, active_bspwm_monitors.pop(primary_monitor_index))

    # step 1, set the primary monitor's padding. the primary monitor contains
    # the menubar, so it should always have padding so it's visible on screen
    primary_bspwm_monitor = active_bspwm_monitors[0]
    Bspwm.set_monitor_padding(primary_bspwm_monitor, padding_for_primary)

    # step 2, setup the virutal desktops for each monitor
    if len(active_bspwm_monitors) > len(desktop_layouts):
        raise f'more than {len(desktop_layouts)} monitors unsupported'
    for desktop_layout, bspwm_monitor in zip(desktop_layouts, active_bspwm_monitors):
        Bspwm.set_desktop_layout(bspwm_monitor, desktop_layout)

    # step 3, if there are any bspwm windows remaining in monitors that aren't
    # enabled anymore, move them to the primary screen
    for bspwm_monitor in bspwm_monitors_to_be_turned_off:
        for window in bspwm_monitor.windows:
            print(f'sending {repr(window)} to {repr(primary_bspwm_monitor)}')
            Bspwm.send_to_monitor(window, primary_bspwm_monitor.name)

    # finally, remove all the inactive monitors
    for bspwm_monitor in bspwm_monitors_to_be_turned_off:
        print(f'removing {repr(bspwm_monitor)}')
        Bspwm.remove_monitor(bspwm_monitor.name)


# badboy from https://config9.com/linux/how-to-create-a-callback-for-monitor-plugged-on-an-intel-graphics/
def udev_event_received(device):
    # TODO: rather than wait a fixed interval waiting for the X screen
    # configuration to get updated whenever a monitor change is detected, we
    # could do something pretty smart:
    #
    # after a change is detected, every N seconds, poll and see if the
    # configuration was changed, and timeout after M seconds.
    # possibly, N: 1, M: 30 or 60
    #
    # but the 3 works pretty well for now
    time.sleep(3)
    on_monitor_change()


if __name__ == '__main__':
    context = pyudev.Context()
    monitor_drm = pyudev.Monitor.from_netlink(context)
    monitor_drm.filter_by(subsystem='drm')
    observer_drm = pyudev.MonitorObserver(monitor_drm, callback=udev_event_received, daemon=False)
    observer_drm.start()
    observer_drm.join()

#on_monitor_change()
