import sys

class StatusWriter(object):
    DEBUG = 1
    INFO  = 2
    WARN  = 3 ; WARNING = 3
    ERROR = 4
    FATAL = 5

    def __init__(
        self,
        logs:list=[sys.stderr],
        reports:list=[sys.stdout],
        loglevel:int=2
    )->None:
        self.logs = logs
        self.reports = reports
        self.loglevel = loglevel

    def _write(self, *args, files:list=[], sep:str="", nl:bool=True)->None:
        for fd in files:
            print(sep.join(args), end="" if not nl else None)

    def log(self, *args, level:int=2, cont:bool=False, **kwargs)->None:
        if level > 0 and level < self.loglevel:
            return None
        level_words = ['|....', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']

        self._write(f"{level_words[0 if cont else level]:<5s} ", *args, files=self.logs, **kwargs)

    def debug(self, *args, **kwargs)->None:
        self.log(*args, level=self.DEBUG, **kwargs)

    def info(self, *args, **kwargs)->None:
        self.log(*args, level=self.INFO, **kwargs)

    def warn(self, *args, **kwargs)->None:
        self.log(*args, level=self.WARN, **kwargs)

    def error(self, *args, **kwargs)->None:
        self.log(*args, level=self.ERROR, **kwargs)
    
    def fatal(self, *args, code:int=111, **kwargs)->None:
        self.log(*args, level=self.FATAL, **kwargs)
        sys.exit(code)
    
    def report(self, *args, **kwargs)->None:
        self._write(*args, files=self.reports, **kwargs)

    