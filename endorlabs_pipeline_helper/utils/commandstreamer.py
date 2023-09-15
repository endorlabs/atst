"""Stream Popen objects
"""

import sys, os, re, time, subprocess, threading


class QueuedText(object):
    """Queue of text lines for use with Streamed Process

    ::example
      proc = StreamedProcess(['ls'])
      stdout_queue = QueuedText()
      proc.run(stdout_handler=stdout.queue_handler())


    Args:
        object (_type_): _description_
    """
    def __init__(self, line_processor=None):
        self.queue = []
        self.line_processor = line_processor

    def _noop(self):
        pass

    def append(self, line:str, line_processor=None):
        if line is None or len(line) == 0:
            return None

        if line_processor is None:
            line_processor = self.line_processor

        if line_processor is not None:
            line = line_processor(line) 

        self.queue.append(line)

    def getline(self):
        return self.queue.pop(0) if len(self.queue) else None

    def queue_handler(self, line_processor=None):
        if line_processor is None:
            line_processor = self.line_processor
        def __queue_handler(line, line_processor=line_processor, **kwargs):
            return self.append(line, line_processor=line_processor)

        return __queue_handler


class StreamedProcess(object):
    def __init__(
        self, 
        command_line:list=[], 
        popen_args:list=[], 
        popen_kwargs:dict={}
    ):
        self.command = command_line
        self.popen_args = popen_args
        self.popen_kwargs = popen_kwargs
        self._finished_flag = None
        self._start = None
        self.process = None
        self.stdout = None
        self.stderr = None
    

    def _stream_hook(self, file_obj:object, write_handler:callable=print, **write_kwargs):
        while not self._finished_flag:
            # note: this means the thread has to force termination through setting a signal
            self._elapsed = time.time() - self._start  # note: if self._start hasn't been set, this will raise an exception
            write_handler(file_obj.readline(), **write_kwargs)

    def _get_print_handler(self, fd:object=sys.stderr):
        def print_handler(line, **kwargs):
            return print(line, file=fd, **kwargs)
        return print_handler

    def run(self, stdout_handler=None, stderr_handler=None, join_timeout=0.5):
        """Runs the process with queues for stdout/stderr

        Args:
            stdout_handler (callable, optional): a callable that filters the line from STDOUT before placing on queue. Defaults to None.
            stderr_handler (callable, optional): a callable that filters the line from STDERR before placing on queue. Defaults to None.
            join_timeout (float, optional): How long after process ends to wait for threads to join. Defaults to 0.5.

        Returns:
            Popen Object: returns the process object for further processing (e.g. getting return code)
        """
        self._finished_flag = False
        self._start = time.time()

        # setup queue handlers
        self.stdout = QueuedText(line_processor=stdout_handler)
        self.stderr = QueuedText(line_processor=stderr_handler)

        # start the process
        self.process = subprocess.Popen(
            self.command, *self.popen_args,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1,  # set up pipes and line buffers
            **self.popen_kwargs)
        self.join_timeout = join_timeout

        # set up the monitoring threads
        # print(dir(self.stdout)) ; exit(1)
        self._stdout_thread = threading.Thread(target=self._stream_hook, args=(self.process.stdout,), kwargs={'write_handler': self.stdout.queue_handler()})
        self._stderr_thread = threading.Thread(target=self._stream_hook, args=(self.process.stderr,), kwargs={'write_handler': self.stderr.queue_handler()})
        self._stdout_thread.start()
        self._stderr_thread.start()

        # return the process object
        return self.process

    def join(self, *args, timeout:float=None, **kwargs):
        if timeout is None:
            timeout = self.join_timeout
        self._finished_flag = True
        self._stderr_thread.join(*args, timeout=timeout, **kwargs)
        self._stdout_thread.join(*args, timeout=timeout, **kwargs)

    def check_join(self, *args, **kwargs)->int:
        result = self.process.poll()
        if result is None:
            return None
        else:
            self.join(*args, **kwargs)
            return self.process.returncode