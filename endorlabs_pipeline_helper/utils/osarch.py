# stdlib
import os

OS_MAP = {
    'darwin': 'macos',
    'gnu/linux': 'linux',
    'linux': 'linux'
}

ARCH_MAP = {}

def get_osarch(osname=None, arch=None):
    uname = os.uname()
    _osname = OS_MAP.get(uname.sysname.lower(), uname.sysname.lower()) if osname is None else osname
    _arch = ARCH_MAP.get(uname.machine.lower(), uname.machine.lower()) if arch is None else arch

    return(_osname, _arch)
