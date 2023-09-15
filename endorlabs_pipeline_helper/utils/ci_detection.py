import os, sys


class CI_Environment(object):
    def __init__(self):
        self.name = ''
        self._path = '.'
        self.current_group = None
        self._group_format = '{message}'
        self._group_end = '--'
        self.setup()

    def start_group(self, title, file=sys.stderr):
        if self.current_group is not None:
            raise ValueError("Can't start a group when one is already started")
        self.current_group = (file, title.replace("\n", ""))
        print(self._group_format.format(message=self.current_group[1]), file=self.current_group[0])

    def end_group(self):
        if self.current_group is None:
            raise ValueError("Can't end a group when when one isn't started")
        print(self._group_end, file=self.current_group[0])
        self.current_group = None

    def setup(self):
        pass
        
        

class CI_GitHub(CI_Environment):
    def setup(self):
        self.name = 'GitHub'
        self.path = os.getenv('GITHUB_WORKSPACE', '.')
        self._group_format = '##[group]{message}'
        self._group_end = '##[endgroup]'



def detected_CI():
    if 'GITHUB_WORKSPACE' in os.environ:
        return CI_GitHub()
    ci = CI_Environment()
    ci.name = 'Unknown CI or non-CI'
    return ci