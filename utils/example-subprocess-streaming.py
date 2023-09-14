from subprocess import Popen, PIPE, TimeoutExpired
from shutil import which
from time import sleep
from sys import stderr as STDERR, stdout as STDOUT
import sys, re, json, time, threading

if __name__ != '__main__':
    raise RuntimeError("This is not a library, do not import")

finished = False

class EC_LogFilter(object):
    re_statusline = re.compile('^\s*(\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d+)-(\d+)\s+([A-Z]+)\s+(.+?)\s+(.+?)\s+(\\{.+\\})\s*$')
    re_project_uuid = re.compile('project uuid ([a-f0-9]{24})')
    re_endorlink = re.compile('(https://app.endorlabs.com/\\S+)')

    def __init__(self):
        self.project_uuid=None
        self.links = []
        self.start = time.time()
        self.elapsed = 0

    def filter_write(self, line, **kwargs):
        # print(f"WRITE req: '{line}' with {kwargs}", file=STDERR)
        self.elapsed = time.time() - self.start
        match = self.re_statusline.search(line)
        if match:
            (the_time, tz_offset, level, location, message, json_data) = match.groups()
            json_data = json.loads(json_data)
            json_data['message_source'] = location
            # print(f"{the_time}\t{level}\t{message}\n{json.dumps(json_data, indent=2)}", file=STDERR)
            print(f"{self.elapsed:9.2f}\t{level:<7s}\t{message}", **kwargs)
       
        match = self.re_project_uuid.search(line)
        if match:
            (uuid,) = match.groups()
            if uuid != self.project_uuid:
                print(f"{self.elapsed:9.2f}\t{'XINFO':<7s}\tset project UUID to {uuid}{'' if self.project_uuid is None else f', was {self.project_uuid}'}", **kwargs)
                self.project_uuid = uuid
        
        match = self.re_endorlink.search(line)
        if match:
            (url,) = match.groups()
            self.links.append(url)

    def filter_writer(self):
        def wrfunc(line, **kwargs):
            self.filter_write(line, **kwargs)

        return wrfunc



def monitor_file(file_obj, linefunc=print, **kwargs):
    global finished
    # print(f"Thread start with {repr(file_obj)} to print with {linefunc} and args {kwargs}", file=STDERR)
    while not finished:
        # note: this means the calling thread will have to stop the sub-thread
        buffer = file_obj.readline().rstrip("\n\r")
        linefunc(buffer, **kwargs)
            
        
    


endorctl = which('endorctl')
start_time = time.time()
ec = Popen(
    ['endorctl', 'scan', '--namespace', 'darren-learn', '--quick-scan', '--verbose', '--languages=javascript'],
    stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True,
    bufsize=1)

# finished = False
# while not finished:
#     try:
#         (out, err) = ec.communicate(timeout=5)
#         # seems to be the whole stream each time?
#         print("O: " + out.decode('utf8'), file=STDERR)
#         print("E: " + err.decode('utf8'), file=STDERR)
#         print("---")
#     except TimeoutExpired as e:
#         print(".", end="", file=STDERR)


# while not finished:
#     try:
#         # sleep(0.5)
#         err = ec.stderr.readline()
#         elapsed = time.time() - start_time
#         # out = ec.stdout.readline()
#         # print("O: " + out.decode('utf8'), file=STDERR, end="")
#         # print("E: " + err, file=STDERR, end="")
#         match = re_statusline.search(err)
#         if match is None:
#             print(f"!{elapsed:9.2f}\t" + err, file=STDERR, end="")
#         else:
#             (the_time, tz_offset, level, location, message, json_data) = match.groups()
#             json_data = json.loads(json_data)
#             json_data['message_source'] = location
#             # print(f"{the_time}\t{level}\t{message}\n{json.dumps(json_data, indent=2)}", file=STDERR)
#             print(f"{elapsed:9.2f}\t{level:<7s}\t{message}", file=STDERR)
#         # print("---", file=STDERR)
#         match = re_project_uuid.search(err)
#         if match:
#             (uuid,) = match.groups()
#             if uuid != project_uuid:
#                 print(f"{elapsed:9.2f}\t{'XINFO':<7s}\tset project UUID to {uuid}{'' if project_uuid is None else f', was {project_uuid}'}")
#                 project_uuid = uuid
#         match = re_endorlink.search(err)
#         if match:
#             (url,) = match.groups()
#             links.append(url)

#     except Exception as e:
#         raise e
    
#     finished = False if ec.poll() is None else True

out_thr = threading.Thread(target=monitor_file, args=(ec.stdout,), kwargs={'file': STDOUT}, daemon=False)
errmon = EC_LogFilter()
err_thr = threading.Thread(target=monitor_file, args=(ec.stderr,), kwargs={'linefunc': errmon.filter_writer(), 'file': STDERR}, daemon=False)
out_thr.start()
err_thr.start()
while not finished:
    try:
        finished = False if ec.poll() is None else True
    except KeyboardInterrupt as e:
        finished=True
        out_thr.join(timeout=0.01)
        err_thr.join(timeout=0.01)
        print("Received SIGINT via keyboard interrupt, exiting with code 120", file=STDERR)
        sys.exit(120)

out_thr.join(timeout=2)
err_thr.join(timeout=2)

# print(ec.stdout.read())
if errmon.project_uuid:
    print(f"UUID {errmon.project_uuid}", file=STDERR)

if errmon.links:
    print("LINKS\n" + json.dumps(errmon.links, indent=2))

print("EXIT with code " + str(ec.returncode), file=STDERR)
