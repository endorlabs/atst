from endorlabs_pipeline_helper.utils.commandstreamer import StreamedProcess

def filter_write(line):
    if line.startswith('INFO'):
        line = line.replace('INFO', '****')
    return(line)

ec = StreamedProcess(['ls'])
# ec.run(stderr_handler=filter_write)
ec.run()
while ec.check_join() is None:
    out = ec.stdout.getline()
    if out is not None and len(out):
        print(ec.stdout.getline(), end="")
    err = ec.stderr.getline()
    if err is not None and len(err):
        print("E:" + ec.stderr.getline(), end="")

exit(ec.process.returncode)