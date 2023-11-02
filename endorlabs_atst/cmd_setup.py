# stdlib
import hashlib, os, subprocess

# installed
import click
import requests ; requests.packages.urllib3.disable_warnings(True)
import semantic_version

# local
from .main import main, Status, CI, CLICK_CONTEXT_SETTINGS
from .utils import osarch
from .utils.statuswriter import TimedProgress
from .utils.commandstreamer import StreamedProcess
from .utils.verdata import endorctl_version


def get_endorctl_latest_data(osname:str, arch:str, endpoint:str='https://api.endorlabs.com/meta/version'):
    Status.debug(f"Getting version info from {endpoint}")
    resp = requests.get(endpoint)
    ver_data = resp.json()
    Status.debug(Status.json(ver_data))

    ver_os = ver_data.get('Service',{}).get('Version', None)
    ver_sum = ver_data.get('ClientChecksums',{}).get(f'ARCH_TYPE_{osname.upper()}_{arch.upper()}', None) 
    return (ver_os, ver_sum)


def download_endorctl(version:str='latest', sha256=None, _dlpath:str=None, _filepath:str='../endorctl'):
    _DL_PATHS = {
        'proxy': 'https://api.endorlabs.com/download/endorlabs/{version}/binaries/endorctl_{version}_{osname}_{arch}',
        'direct': 'https://storage.googleapis.com/endorlabs/{version}/binaries/endorctl_{version}_{osname}_{arch}'
    }
    if _dlpath is None:
        _dlpath = _DL_PATHS['proxy']
    
    osname = CI.runner_os 
    arch = CI.runner_arch

    if version == 'latest' or version is None:
        # get version and sum from API
        Status.info("Acquiring version data from API")
        (version, _sha256) = get_endorctl_latest_data(osname, arch)
        sha256 = _sha256 if sha256 is None else sha256
    elif sha256 is None:
        # Try lookup
        verkey = f"{version}_{osname}_{arch}".lstrip('v')
        if verkey in endorctl_version:
            sha256 = endorctl_version[verkey]['sha256']
            Status.info(f"Found digest data {verkey}: {sha256}")
        else:
            Status.warn(f"Could not find SHA256 digest for '{verkey}'")

    sha256 is None and Status.warn("no SHA256 sum data, will skip verification")
    if not version.startswith('v'):
        version = f"v{version}"

    dlpath = _dlpath.format(osname=osname, version=version, arch=arch)
    if osname == 'windows':
        dlpath += '.exe'
    Status.debug("Download path: " + dlpath)

    try:
        dlhash = hashlib.sha256()
        dl = requests.get(dlpath, stream=True)
        dl.raise_for_status()

        prog_updater = TimedProgress(every=10)
        prog_updater.start(f"Downloading endorctl {version} for {osname} on {arch}")
        dl_size = 0
        with open(_filepath, 'wb') as fd:
            for count, buffer in enumerate(dl.iter_content(chunk_size=102_400, decode_unicode=False)):
                # download 100k at a time
                fd.write(buffer)
                dl_size += len(buffer)
                prog_updater.update(f"Still downloading -- {dl_size/1_048_576:.0f} MiB in " + '{elapsed}' + f" ({dl_size/1_048_576/prog_updater.elapsed():.2f} MiB/s)")
                dlhash.update(buffer)

        Status.info(f"Download completed: {dl_size/1_048_576:.2f} MiB in {prog_updater.elapsed():.2f}s ({dl_size/1_048_576/prog_updater.elapsed():.2f} MiB/s)")
        digest = dlhash.hexdigest()
        Status.debug(f"Digest = {digest}, of type {type(digest)}")
        if sha256 is not None:
            if int(sha256, 16) == int(digest, 16):
                Status.info(f"Verified download matches SHA256 {sha256}")
                os.chmod(_filepath, 0o750)
                Status.info(f"Successfully downloaded to '{_filepath}'")
            else:
                Status.error(f"Verification failed; expected {sha256}, got {digest}")
                raise ValueError("SHA256 sum mismatch")
    except Exception as e:
        Status.error(f"Unable to download endorctl: {str(e)}")
        if Status.loglevel <= Status.DEBUG:
            raise e
        os.path.isfile(_filepath) and os.unlink(_filepath)
        Status.fatal(f"Failed fetching endorctl, removed {_filepath} if it existed")


def check_endorctl_version(command_path:str, ver_rule:str='>=1.5'):
    semver=semantic_version.NpmSpec(ver_rule)
    Status.debug(f"Running {command_path} to check version")
    ec = subprocess.run([command_path, '--version'], capture_output=True)
    detected_version = semantic_version.Version(ec.stdout.decode('utf8').lower().removeprefix('endorctl version v'))
    Status.debug("endorctl --version output: " + str(detected_version))
    Status.debug(f"Version {detected_version} {'matches' if semver.match(detected_version) else 'does not match'} {ver_rule}")
    return (detected_version, semver.match(detected_version))
        

def _setup(ctx, endorlabs_version, endorlabs_sha256sum, endorlabs_command_path, force_download, namespace, auth):
    """Implementation wrapper for setup() below
    """
    Status.debug(f"subcommand: setup")
    Status.debug(f"Requested version {endorlabs_version} with SHA256 '{'' if endorlabs_sha256sum is None else endorlabs_sha256sum}'")
    if endorlabs_command_path is None:
        endorlabs_command_path = os.path.join(ctx.obj['scriptdir'], 'endorctl')

    need_to_download = True
    if os.path.exists(endorlabs_command_path):
        (version, complies) = check_endorctl_version(endorlabs_command_path, endorlabs_version if endorlabs_version != 'latest' else '>=1.6')
        if complies and not force_download:
            # TODO not sure if this is right, might want to try to see if _current_ version is newer and still complies; could get complex
            Status.info(f"Existing '{endorlabs_command_path}' @{version} is compliant, leaving in place") 
            need_to_download = False 
        elif complies:
            Status.warn(f"Replacing existing '{endorlabs_command_path}' even though it's version-compliant (@{version}) (force_download)")
    
    if need_to_download:
        Status.report(CI.start_group("Downloading endorctl"))
        download_endorctl(endorlabs_version, endorlabs_sha256sum, _filepath=endorlabs_command_path)
        Status.report(CI.end_group())

    CI.prepend_env_path(ctx.obj['scriptdir'])
    if namespace is not None:
        CI.set_env('ENDOR_NAMESPACE', namespace)
    if auth is not None:
        try:
            (schema, rule) = auth.strip().split(':', maxsplit=1)
            if schema.lower() == 'api':
                Status.debug('extracting secret and key from api schema argument')
                (api_key, api_secret) = rule.strip().split(':', maxsplit=1)
                CI.set_env('ENDOR_API_CREDENTIALS_KEY', api_key)
                CI.set_env('ENDOR_API_CREDENTIALS_SECRET', api_secret)
                Status.debug(f"Set key='{api_key}' with secret '{api_secret}' from '{rule}'")
        except ValueError as e:
            Status.error(f"Invalid schema spec '{auth}'")  # TODO redact sensitive data?
            Status.debug(str(e))

    # TODO setup endorctl config with namespace/etc


@main.command(context_settings=CLICK_CONTEXT_SETTINGS)
@click.option(
    '--endorlabs-version',
    envvar='ENDORLABS_VERSION',
    default='latest')
@click.option(
    '--endorlabs-sha256sum',
    envvar='ENDORLABS_SHA256SUM')
@click.option(
    '--endorlabs-command-path',
    envvar='ENDORLABS_COMMAND_PATH',
    hidden=True)
@click.option(
    '--force-download',
    envvar='ENDORLABS_FORCE_DOWNLOAD',
    is_flag=True,
    hidden=True)
@click.option(
    '--namespace',
    envvar='ENDOR_NAMESPACE',
    required=False)
@click.option(
    '--auth',
    help="auth data for endor; follows SCHEMA:AUTHDATA e.g. 'api:API_KEY:API_SECRET'")
# TODO add env options so that API key and SECRET are picked up from env if set
@click.pass_context
def setup(*args, **kwargs):
    """Setup the CI environment to use Endor Labs
    """
    _setup(*args, **kwargs)
