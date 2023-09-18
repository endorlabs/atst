#stdlib
import os, shlex, sys, re, json

#installed
import click

#local
from .main import main, Status, CI, CLICK_CONTEXT_SETTINGS
from .cmd_setup import check_endorctl_version, download_endorctl
from .utils.commandstreamer import StreamedProcess


# VERBOSE_LINE_REGEX = re.compile("^(\\d{4}-\\d{2}\\d{2}-.+?)\\s+([A-Z]+)\\s+(\\S+)\\s+(.+)$")
VERBOSE_LINE_REGEX = re.compile("^(\\d{4}-\\d{2}-\\d{2}T.+?)\\s+([A-Z]+)\\s+(\\S+)\\s+(.+)")
XDATA_REGEX = re.compile("(\\{.+\\})")
PROJECT_UUID = None
ENDORCTL_WARNINGS = []
ENDORCTL_ERRORS = []

def endorctl_log_filter(filehandle):
    def _filter(line):
        global PROJECT_UUID, ENDORCTL_ERRORS, ENDORCTL_WARNINGS
        vmatch = VERBOSE_LINE_REGEX.match(line)
        if vmatch:
            (timestamp, level, location, message) = vmatch.groups()
            xmatch = XDATA_REGEX.search(message)
            xdata = ''
            if xmatch:
                xdata = xmatch.group(1)
                if PROJECT_UUID is None:
                    xdata_dict = json.loads(xdata)
                    PROJECT_UUID = xdata_dict.get('project_uuid', None)
                message = message.replace(xdata,'').strip()
            # Status.debug(f"{line}\n\t{level:<7s}::{message}::{location}{'::' + Status.json(xdata) if xdata else ''}")
            out = f"{level:<7s} {message}\n"
            if level.startswith('WARN'):
                ENDORCTL_WARNINGS.append(out)
            elif level.startswith('ERR'):
                ENDORCTL_ERRORS.append(out)
        else:
            out = line
        filehandle.write(line)
        return out
    return _filter


def run_endorctl(endorctl_path, *endorctl_args, retry_count=0, extra_env = {}):
    _retry_limit = 1
    detected_endorctl_version = None
    if retry_count > 0:
        Status.info(f"Retrying endorctl run, attempt {retry_count}")
    try:
        (detected_endorctl_version, semver_match) = check_endorctl_version(endorctl_path)  # TODO option for version enforcement
        Status.info(f"Found {endorctl_path} @v{detected_endorctl_version}")
    except FileNotFoundError as e:
        Status.warn(f"{e}")
        Status.warn(f"`{sys.argv[0]} setup` doesn't appear to have run; downloading endorctl but NOT completing setup")
        download_endorctl(_filepath=endorctl_path)

    if (detected_endorctl_version is None or not semver_match) and retry_count < _retry_limit:
        return run_endorctl(endorctl_path, *endorctl_args, extra_env=extra_env, retry_count=retry_count+1)

    ## now actually run the process
    retcode = 1
    try:
        ec_cmd = [endorctl_path] + list(endorctl_args)
        # ec_env = dict( {(k,os.getenv(k)) for k in os.environ if k.startswith('ENDOR_')} ) | extra_env
        ec_env = dict({(k,os.getenv(k)) for k in os.environ}) | extra_env
        Status.debug(f"Running {ec_cmd} with environment: {Status.json(ec_env)}")
        ec = StreamedProcess(ec_cmd, popen_kwargs={'env': ec_env})
        Status.info(f"Starting {' '.join([shlex.quote(x) for x in ec_cmd])}")

        with open('endorscan.log', 'a') as logfile:  # TODO make logfile configurable
            ec.run(stderr_handler=endorctl_log_filter(logfile))
            print(CI.start_group("endorctl command"), file=sys.stderr)
            while ec.check_join() is None:
                if ec.stderr.queue:
                    print(ec.stderr.getline(), file=sys.stderr, end="")  # TODO filter endor lines
            print(CI.end_group(), file=sys.stderr)
            stdout = ''.join(ec.stdout.queue).rstrip()
            if stdout:
                # print all of STDOUT
                print(CI.start_group("endorctl results"), file=sys.stderr); sys.stderr.flush()
                print(stdout); sys.stdout.flush()
                print(CI.end_group(), file=sys.stderr); sys.stderr.flush()
        retcode = ec.process.returncode

    except Exception as e:
        Status
        raise e

    CI.current_group is not None and print(CI.end_group(), file=sys.stderr)
    if retcode:
        Status.warn(f"{endorctl_path} exited with code {retcode}")
    else:
        Status.info(f"{endorctl_path} completed successsfully")
    return retcode



@main.command(context_settings=CLICK_CONTEXT_SETTINGS)
@click.argument(
    'endorctl_args',
    nargs=0-1)
@click.pass_context
def ctl(ctx, endorctl_args):
    """Run `endorctl` in a CI wrapper
    """
    Status.debug(f"Started subcommand: ctl {endorctl_args}")
    endorctl_path = os.path.join(ctx.obj['scriptdir'], 'endorctl')
    exitcode = run_endorctl(endorctl_path, *endorctl_args, extra_env={'ENDOR_LOG_VERBOSE': 'true'})

    ## Summarize endorctl errors/warnings
    if PROJECT_UUID is not None:
        Status.info(f"Endor Labs Project UUID: {PROJECT_UUID}")
    if ENDORCTL_ERRORS or ENDORCTL_WARNINGS:
        Status.warn("endorctl produced:", retain=False)
        if ENDORCTL_ERRORS:
            Status.log(f"{len(ENDORCTL_ERRORS)} errors:")
            for err in ENDORCTL_ERRORS:
                Status.log(err.strip(), cont=True)
        if ENDORCTL_WARNINGS:
            Status.log(f"{len(ENDORCTL_WARNINGS)} warnings:")
            for wrn in ENDORCTL_WARNINGS:
                Status.log(wrn.strip(), cont=True)
    
    ## Summarize ATST errors/warnings
    if Status.errors or Status.warnings:
        Status.warn("ATST also had:", retain=False)
        Status.warnings.pop(-1)  # remove the warning we just issued ;)
        if Status.errors:
            Status.log(f"{len(Status.errors)} ERROR messages:", cont=True)
            for err in Status.errors:
                Status.log(err, level=0)
        if Status.warnings:
            Status.log(f"{len(Status.warnings)} WARN messages:", cont=True)
            for wrn in Status.warnings:
                Status.log(wrn, level=0)
    sys.exit(exitcode)
    
        

