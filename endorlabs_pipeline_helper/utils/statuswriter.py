import sys
import json as jsonlib
import time

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
        self.errors = []
        self.warnings = []

    def _write(self, *args, files:list=[], sep:str="", nl:bool=True)->None:
        for fd in files:
            print(sep.join(args), end="" if not nl else None)

    def log(self, *args, level:int=2, cont:bool=False, retain:bool=True, **kwargs)->None:
        """General log to output

        Args:
            level (int, optional): Log Level to log at. Defaults to 2 (INFO).
            cont (bool, optional): Continuation line; if True, line prefix will be a continuation indicator. Defaults to False.
            retain (bool, optional): Retain errror/warning. Defaults to True.

        Returns:
            _type_: _description_
        """
        if level > 0 and level < self.loglevel:
            return None
        level_words = ['|....', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL']
        logprefix = f"{level_words[0 if cont else level]:<5s} " 
        if level == self.ERROR and retain:
            self.errors.append(logprefix + " ".join(args))
        elif level == self.WARNING and retain:
            self.warnings.append(logprefix + " ".join(args))

        self._write(logprefix, *args, files=self.logs, **kwargs)

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

    def json(self, doc:dict, indent:int=2, **kwargs)->str:
        return jsonlib.dumps(doc, indent=indent, **kwargs)


class TimedProgress(object):
    def __init__(self, every:float=10, writer=None, write_level:int=StatusWriter.INFO):
        self.delay = every
        self.writer = StatusWriter() if writer is None else writer
        self.level = write_level
        self.start_time = 0
        self.last_update = 0

    def start(self, message:str=None, *args, **kwargs):
        self.start_time = time.time()
        if message is not None:
            self.update(message, *args, **kwargs)

    def update(self, message:str=None, *args, **kwargs):
        now = time.time()
        if now - self.last_update < self.delay:
            return None
        self.last_update = now
        if message is None:
            self.writer.log(f"Operation still in progress after {now-self.start:<.1f}s", *args, level=self.level, **kwargs)
        else:
            self.writer.log(message.format(elapsed=f"{now-self.start_time:<.1f}s"), *args, level=self.level, **kwargs)

    def elapsed(self):
        return time.time() - self.start_time