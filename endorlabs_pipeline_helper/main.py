# stdlib
import os

# local
from .utils import StatusWriter
from . import __version__ as __package_version

# installed
import click

CONFIG_PREFIX = 'ATST'
CLICK_CONTEXT_SETTINGS = { 'auto_envvar_prefix': CONFIG_PREFIX }

Status = StatusWriter()

@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_context
def main(ctx):
    ctx.ensure_object(dict)
    if os.getenv('DEBUG', False) or os.getenv(f'{CONFIG_PREFIX}_DEBUG', False):
        Status.loglevel = Status.DEBUG
    
    if Status.loglevel <= Status.DEBUG:
        for pth in os.getenv('PATH','').split(':'):
            if os.access(pth, os.W_OK):
                Status.debug(f"'{pth}' is{'' if os.access(pth, os.W_OK) else ' NOT'} writable")
    Status.info(f"Starting {ctx.info_name} {__package_version}")
