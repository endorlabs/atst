import os, sys


class CI_Environment(object):
    def __init__(self):
        self.name = ''
        self._path = '.'
        self.current_group = None
        self._group_format = '{message}'
        self._group_end = '--'
        self.setup()

    def _append_to_file(self, filename:str, *lines):
        with open(filename, 'a') as target:
            for line in lines:
                target.print(line)
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

    def set_env_path(self, newval:str):
        pass

    def prepend_env_path(self, newpath:str):
        pth = os.getenv('PATH','') 
        pth += f"{':' if len(pth) else ''}{newpath}"
        return self.set_env_path(pth)

    def setup(self):
        pass

        
        

class CI_GitHub(CI_Environment):
    def setup(self):
        self.name = 'GitHub'
        self.path = os.getenv('GITHUB_WORKSPACE', '.')
        self._group_format = '##[group]{message}'
        self._group_end = '##[endgroup]'

    def set_env_path(self, newval:str):
        self._append_to_file(os.getenv('GITHUB_PATH', None), newval)
        return newval


def detected_CI():
    if 'GITHUB_WORKSPACE' in os.environ:
        return CI_GitHub()
    ci = CI_Environment()
    ci.name = 'Unknown CI or non-CI'
    return ci