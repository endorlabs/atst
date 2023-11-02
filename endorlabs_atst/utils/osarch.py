# stdlib
import os, platform

OS_MAP = {
    'darwin': 'macos',
    'gnu/linux': 'linux',
    'linux': 'linux',
    'windows': 'windows'
}

ARCH_MAP = {
    'x86_64': 'amd64',
    'x64': 'amd64',
    'aarch64': 'arm64',
    'arm64': 'arm64',
    'amd64': 'amd64',
}

def get_osarch(osname=None, arch=None):
    uname = platform.uname()
    _osname = OS_MAP.get(uname.system.lower(), uname.system.lower()) if osname is None else osname
    _arch = ARCH_MAP.get(uname.machine.lower(), uname.machine.lower()) if arch is None else arch

    return(_osname, _arch)
