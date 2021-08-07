"""
This modules contains implementations of helper functions specific to
"pure" (i.e., non-interactive) Python scripts.

**Note**: `davos` does not currently support pure Python, but will begin
to do so in a near-future version.
"""

__all__ = [
    'auto_restart_rerun',
    'generate_parser_func',
    'prompt_restart_rerun_buttons'
]


import locale
import shlex
import signal
import sys
from contextlib import redirect_stdout
from io import StringIO
from subprocess import CalledProcessError, PIPE, Popen


def _activate_helper(smuggle_func, parser_func):
    """
    Pure Python implementation of `_activate_helper`.

    Raises `NotImplementedError` whenever called, as `davos` does not
    yet support non-interactive Python environments.

    Parameters
    ----------
    smuggle_func : callable
        Function to be injected into the module namespace under the
        name "`smuggle`" (typically, `davos.core.core.smuggle`).
    parser_func : callable
        Function called to parse the Python module as plain text and
        replace `smuggle` statements with the `smuggle()` function.

    Raises
    -------
    NotImplementedError
        In all cases.
    """
    raise NotImplementedError(
        "davos does not yet support non-interactive Python environments"
    )


def _check_conda_avail_helper():
    """
    Check whether the `conda` executable is available.

    Pure Python implementation of helper function for
    `davos.core.core.check_conda`. Tries to access the `conda`
    executable by running `conda list IPython`. If successful, returns
    the (suppressed) stdout generated by the command. Otherwise, returns
    `None`.

    Returns
    -------
    str or None
        If `conda list IPython` executes successfully, the captured
        stdout. Otherwise, `None`.

    Raises
    ------
    subprocess.CalledProcessError
        If the `conda` executable is not available.

    See Also
    --------
    davos.core.core.check_conda : core function that calls this helper.
    """
    try:
        with redirect_stdout(StringIO()) as conda_list_output:
            # using `conda list` instead of a more straightforward
            # command so stdout is formatted the same as the IPython
            # implementation (which must use `conda list`)
            _run_shell_command_helper('conda list Python')
    except CalledProcessError:
        return None
    return conda_list_output.getvalue()


def _deactivate_helper(smuggle_func, parser_func):
    """
    Pure Python implementation of `_activate_helper`.

    Raises `NotImplementedError` whenever called, as `davos` does not
    yet support non-interactive Python environments.

    Parameters
    ----------
    smuggle_func : callable
    parser_func : callable

    Raises
    -------
    NotImplementedError
        In all cases.
    """
    raise NotImplementedError(
        "davos does not yet support non-interactive Python environments"
    )


def _run_shell_command_helper(command):
    """
    Run a shell command in a subprocess, piping stdout & stderr.

    Pure Python implementation of helper function for
    `davos.core.core.run_shell_command`. stdout & stderr streams are
    captured or suppressed by the outer function. If the command runs
    successfully, return its exit status (`0`). Otherwise, raise an
    error.

    Parameters
    ----------
    command : str
        The command to execute.

    Returns
    -------
    int
        The exit code of the command. This will always be `0` if the
        function returns. Otherwise, an error is raised.

    Raises
    ------
    subprocess.CalledProcessError :
        If the command returned a non-zero exit status.
    """
    cmd = shlex.split(command)
    process = Popen(cmd, stdout=PIPE, stderr=PIPE,
                    encoding=locale.getpreferredencoding())
    try:
        while True:
            retcode = process.poll()
            if retcode is None:
                output = process.stdout.readline()
                if output:
                    sys.stdout.write(output)
            elif retcode != 0:
                # processed returned with non-zero exit status
                raise CalledProcessError(returncode=retcode, cmd=cmd)
    except KeyboardInterrupt:
        # forward CTRL + C to process before raising
        process.send_signal(signal.SIGINT)
        raise


def auto_restart_rerun(pkgs):
    """
    Pure Python implementation of `auto_restart_rerun`.

    Raises `NotImplementedError` whenever called, as `davos` does not
    yet support non-interactive Python environments.

    Parameters
    ----------
    pkgs : list of str
        Packages that could not be reloaded without restarting the
        runtime.

    Raises
    -------
    NotImplementedError
        In all cases.
    """
    raise NotImplementedError(
        "automatic rerunning not available in non-interactive Python (this "
        "function should not be reachable through normal use)."
    )


def generate_parser_func(line_parser):
    """
    Pure Python implementation of `generate_parser_func`.

    Raises `NotImplementedError` whenever called, as `davos` does not
    yet support non-interactive Python environments.

    Parameters
    ----------
    line_parser : callable
        Function that parses a single line of user code (typically,
        `davos.core.core.parse_line`).

    Raises
    -------
    NotImplementedError
        In all cases.
    """
    raise NotImplementedError(
        "davos does not yet support non-interactive Python environments"
    )


def prompt_restart_rerun_buttons(pkgs):
    """
    Pure Python implementation of `prompt_restart_rerun_buttons`.

    Raises `NotImplementedError` whenever called, as button-based input
    prompts are not available outside notebook environments.

    Parameters
    ----------
    pkgs : list of str
        Packages that could not be reloaded without restarting the
        runtime.

    Raises
    -------
    NotImplementedError
        In all cases.
    """
    raise NotImplementedError(
        "button-based user input prompts are not available in non-interactive "
        "Python (this function should not be reachable through normal use)."
    )