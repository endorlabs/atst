from endorlabs_pipeline_helper.utils.commandstreamer import StreamedProcess

def filter_write(line):
    if line.startswith('INFO'):
        line = line.replace('INFO', '****')
    return(line)

ec = StreamedProcess(['ls'])
ec.run(stderr_handler=filter_write)