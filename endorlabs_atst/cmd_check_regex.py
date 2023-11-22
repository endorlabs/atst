# stdlib
import os
import contextlib
# installed
import click
import re2
#local
from .main import main, Status, CI, CLICK_CONTEXT_SETTINGS


@contextlib.contextmanager
def dirpath(path):
    original = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(original)


def _check_regex(ctx, exclude_pattern, include_pattern, hide_exclude, hide_include, hide_default, path=os.path.realpath(os.getcwd())):
    try:
        _data = ['exclude-pattern', exclude_pattern]
        exclude_regex = re2.compile(exclude_pattern) if exclude_pattern is not None else None
        _data = ['include-pattern', include_pattern]
        include_regex = re2.compile(include_pattern) if include_pattern is not None else None
    except re2.error as err:
        Status.fatal(f"unable to parse {_data[0]} '{_data[1]}' as valid RE2 expression: {err.args[0].decode('utf8')}")

    if hide_default and hide_exclude and hide_include:
        Status.debug("Skipping scan because all results are suppressed")
        exit(0)  # no point in actually scanning of all results are suppressed

    path = os.path.realpath(path)
    Status.info(f"Scanning starting with '{path}' as base")
    with dirpath(path):
        for start_dir, dirs, files in os.walk('.'):
            Status.debug(f"in {start_dir}; dirs: {dirs}; - files: {files}")
            for pth in [start_dir] + [os.path.join(start_dir, p) for p in files]:
                pth = pth[2:]
                exclude_match = None if exclude_regex is None else exclude_regex.search(pth)
                include_match = None if include_regex is None else include_regex.search(pth)

                if exclude_match and not include_match and not hide_exclude:
                    print(f"EXCLUDE:{pth}:")
                elif exclude_match and include_match and not hide_include:
                    print(f"INCLUDE:{pth}:")
                elif not hide_default:
                    print(f"DEFAULT:{pth}:")


@main.command(context_settings=CLICK_CONTEXT_SETTINGS)
@click.option('--exclude-pattern',
    help="Pattern to exclude in format passed to endorctl --exclude")
@click.option('--include-pattern',
    help="Pattern to include in format passed to endorctl --include")
@click.option('--hide-exclude', is_flag=True,
    help="Don't print EXCLUDE lines")
@click.option('--hide-include', is_flag=True,
    help="Don't print INCLUDE lines")
@click.option('--hide-default', is_flag=True,
    help="Don't print DEFAULT lines")
@click.argument('path', default=os.path.realpath(os.getcwd()))
@click.pass_context
def check_regex(ctx, *args, **kwargs):
    """
    BETA - Check include/exclude regex against paths.
    
    Checks children of PATH against regex patterns and prints which files will be
    included. PATH defaults to the current directory if not provided.
    
    \b
    Output is in format `ACTION:PATH:` where ACTION is one of:
      - DEFAULT (this path is included by default)
      - INCLUDE (this path would have been excluded, but the include pattern overrides)
      - EXCLUDE (this path is excluded)

    NOTE: this is an *estimation* of what endorctl will do
    """
    _check_regex(ctx, *args, **kwargs)