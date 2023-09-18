import os, sys, shlex, time, re
import warnings

# local
from .osarch import get_osarch, OS_MAP, ARCH_MAP

class CI_Environment(object):
    def __init__(self):
        self.name = ''
        self._path = '.'
        self.current_group = None
        self._group_format = '---- {message}'
        self._group_end = '----'
        self._os = None
        self._arch = None
        self._env = {}
        self.setup()

    def _append_to_file(self, filename:str, *lines):
        with open(filename, 'a') as target:
            target.writelines(lines)
        return None

    def start_group(self, title):
        if self.current_group is not None:
            raise ValueError("Can't start a group when one is already started")
        self.current_group = title.replace("\n", "")
        return self._group_format.format(message=self.current_group)

    def end_group(self):
        if self.current_group is None:
            raise ValueError("Can't end a group when when one isn't started")
        self.current_group = None
        return self._group_end

    def set_env(self, name:str, value:object):
        warnings.warn(f"Can't set environment persistently in a {self.name}", RuntimeWarning)
        self._env[name] = value


    def set_env_path(self, newval:str):
        pass

    def prepend_env_path(self, newpath:str):
        pth = os.getenv('PATH','') 
        pth += f"{':' if len(pth) else ''}{newpath}"
        return self.set_env_path(pth)

    @property
    def runner_os(self):
        if self._os is None:
            (self._os, self._arch) = get_osarch()
        return self._os

    @property
    def runner_arch(self):
        if self._arch is None:
            (self._os, self._arch) = get_osarch()
        return self._arch

    @property
    def repo_dir(self):
        return os.path.abspath('.')

    def setup(self):
        pass
        

class CI_GitHub(CI_Environment):
    def setup(self):
        self.name = 'GitHub'
        self.path = os.getenv('GITHUB_WORKSPACE', '.')
        self._group_format = '##[group]{message}'
        self._group_end = '##[endgroup]'

    def set_env_path(self, newval:str):
        self._append_to_file(os.getenv('GITHUB_PATH', None), newval + "\n")
        return newval

    @property
    def runner_os(self):
        if self._os is None:
            self._os = OS_MAP.get(os.getenv('RUNNER_OS', '').lower().strip(), None)
        if self._os is None:  # the env didn't work, fall back
            super().runner_os
        return self._os

    @property
    def runner_arch(self):
        if self._arch is None:
            self._arch = ARCH_MAP.get(os.getenv('RUNNER_ARCH', '').lower().strip(), None)
        if self._os is None:  # the env didn't work, fall back
            super().runner_arch
        return self._arch

    def set_env(self, name:str, value:object):
       return self._append_to_file(os.getenv('GITHUB_ENV', None), f"{name}={shlex.quote(str(value))}\n")


class CI_GitLab(CI_Environment):
    def setup(self):
        self.name = 'GitLab'
        self.path = os.getenv('CI_PROJECT_DIR', '.')
        self._group_format = "\033[0Ksection_start:{id}\r\033[0K{message}"
        self._group_end = "\033[0Ksection_end:{id}\r\033[0K"

    def start_group(self, title):
        if self.current_group is not None:
            raise ValueError("Can't start a group when one is already started")
        name = re.sub('\\W', '_', title).strip('_')
        self.current_group = str(int(time.time())) + ":" + name
        return self._group_format.format(message=title, id=self.current_group)

    def end_group(self):
        if self.current_group is None:
            raise ValueError("Can't end a group when when one isn't started")
        retval = self._group_end.format(id=self.current_group)
        self.current_group = None
        return retval

    @property
    def repo_dir(self):
        repo = os.getenv('CI_PROJECT_DIR', None)
        if repo is None:
            repo = super().repo_dir
        return os.path.abspath(repo)



def detected_CI():
    if 'GITHUB_WORKSPACE' in os.environ and os.getenv('GITHUB_ACTIONS', '').upper() == "TRUE":
        return CI_GitHub()
    if 'GITLAB_CI' in os.environ:
        return CI_GitLab()

    ci = CI_Environment()
    ci.name = 'Unknown CI or non-CI'
    return ci