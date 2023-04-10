# TODO: add module docstring
import atexit
import os
import shutil
import sys
from os.path import expandvars
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import ipykernel
import requests
from urllib.parse import urljoin, urlparse

from davos import config
from davos.core.core import prompt_input, run_shell_command
from davos.core.exceptions import DavosProjectError


__all__ = ['Project']


DAVOS_CONFIG_DIR = Path.home().joinpath('.davos')
DAVOS_PROJECT_DIR = DAVOS_CONFIG_DIR.joinpath('projects')
PATHSEP = os.sep               # '/' for Unix, '\' for Windows
PATHSEP_REPLACEMENT = "___"    # safe replacement for os.sep in dir name
SITE_PACKAGES_SUFFIX = PATHSEP.join((
    'lib',
    f'python{sys.version_info.major}.{sys.version_info.minor}',
    'site-packages'
))


DAVOS_CONFIG_DIR.mkdir(parents=False, exist_ok=True)


class ProjectChecker(type):
    """TODO: add metaclass docstring"""
    def __call__(cls, name):
        cls_to_init = ConcreteProject
        # if user passed a pathlib.Path, convert it to a str so it can
        # be properly expanded, substituted, resolved, etc. below
        name = str(name)
        if PATHSEP in name:
            # `name` is a path to a notebook file, either
            # Project.default() (path to current notebook) or
            # user-specified. File doesn't *have* to exist at this point
            # (will be an AbstractProject, if not), but must at least
            # point to what could eventually be a notebook
            name_path = Path(expandvars(name)).expanduser().resolve(strict=False)
            if name_path.suffix != '.ipynb' or name_path.is_dir():
                # file doesn't have to exist at this point (can be an AbstractProject)
                raise DavosProjectError(
                    f"Invalid project name: '{name}' (which resolves to "
                    f"'{name_path}'). Project names may be either a simple "
                    f"name (without '{PATHSEP}') or a path to a Jupyter "
                    f"notebook (.ipynb) file."
                )
            elif not name_path.is_file():
                cls_to_init = AbstractProject
            name = str(name_path)
        elif PATHSEP_REPLACEMENT in name:
            # `name` is a path-like project directory name read from
            # DAVOS_PROJECT_DIR. Convert back to normal path format to
            # check whether it exists, but don't want to do any
            # validation here in case user somehow ended up with
            # malformed Project dir name, since that could cause
            # incessant errors until manually fixed. Instead, just make
            # it an AbstractProject and let user rename or delete it
            # via davos
            name_path = Path(f"{name.replace(PATHSEP_REPLACEMENT, PATHSEP)}.ipynb")
            if not name_path.is_file():
                cls_to_init = AbstractProject
            name = str(name_path)
        # `name` passed to __init__ is now a str: either a simple name
        # or a fully substituted path to a .ipynb file
        return type.__call__(cls_to_init, name)


class Project(metaclass=ProjectChecker):
    """
    # TODO: add docstring
    A pseudo-environment associated with a particular (set of)
    davos-enhanced notebook(s)
    """
    def __init__(self, name):
        """
        TODO: add docstring, note difference between what name can be
         passed as vs what it is when __init__ is run due to metaclass
        """
        self._set_names(name)
        self.project_dir.mkdir(parents=False, exist_ok=True)
        atexit.register(cleanup_project_dir_atexit, self.project_dir)

    def __del__(self):
        """
        TODO: add docstring -- if project dir is empty, remove when
         reference count drops to 0, including at end of session
         """
        try:
            self.project_dir.rmdir()
        except OSError:
            pass

    def __repr__(self):
        return f"Project('{self.name}')"

    def _set_names(self, name):
        """
        TODO: add docstring -- separate method so it can be called when
         renaming project to update names
        """
        self.name = name
        self.safe_name = name.replace(PATHSEP, PATHSEP_REPLACEMENT).replace('.ipynb', '')
        self.project_dir = DAVOS_PROJECT_DIR.joinpath(self.safe_name)
        self.site_packages_dir = self.project_dir.joinpath(SITE_PACKAGES_SUFFIX)

    def remove(self, yes=False):
        """
        TODO: add docstring remove the project and all installed
         packages. should prompt for confirmation, but accept "yes" arg
         to bypass
        """
        if not yes:
            prompt = f"Remove project '{self.name} and all installed packages?"
            confirmed = prompt_input(prompt, default='n')
            if not confirmed:
                print(f"{self.name} not removed")
                return
        print(f"Removing {self.project_dir}...")
        shutil.rmtree(self.project_dir)

    def rename(self, new_name):
        """rename the project directory, possibly due to renaming/moving notebook"""
        raise NotImplementedError

    def update_name(self):
        """update the project's name to the current notebook name"""
        raise NotImplementedError


class AbstractProject(Project):
    """TODO: add docstring"""
    def __getattr__(self, item):
        if hasattr(ConcreteProject, item):
            msg = f"'{item}' is not supported for abstract projects"
        else:
            msg = f"'{self.__class__.__name__}' object has no attribute '{item}'"
        raise AttributeError(msg)

    def __repr__(self):
        return f"AbstractProject('{self.name}')"


class ConcreteProject(Project):
    """TODO: add docstring"""
    def __init__(self, name):
        super().__init__(name)

    @property
    def installed_packages(self):
        """pip-freeze-like list of installed packages"""
        raise NotImplementedError


def get_notebook_path():
    # TODO: add docstring
    """get the absolute path to the current notebook"""
    kernel_filepath = ipykernel.connect.get_connection_file()
    kernel_id = kernel_filepath.split('/kernel-')[-1].split('.json')[0]

    running_nbservers_stdout = run_shell_command('jupyter notebook list',
                                                 live_stdout=False)
    for line in running_nbservers_stdout.splitlines():
        # should only need to exclude first line ("Currently running
        # servers:"), but handle safely in case output format changes in
        # the future
        if not line.strip().startswith('http'):
            continue

        nbserver_url, nbserver_root_dir = line.split('::')
        nbserver_url = nbserver_url.strip()
        nbserver_root_dir = nbserver_root_dir.strip()

        notebook_api_url = urljoin(nbserver_url, '/api/sessions')
        parsed_url = urlparse(nbserver_url)
        if parsed_url.query:
            params = {'token': parsed_url.query.removeprefix('token=')}
        else:
            params = None

        # TODO: add exception handling, 403 handling, etc.
        response = requests.get(notebook_api_url, params=params, timeout=10)
        for session in response.json():
            if session['kernel']['id'] == kernel_id:
                if config.environment == 'Colaboratory':
                    # Colab notebooks don't actually live on Colab VM
                    # filesystem, so just use notebook name
                    return unquote(session['notebook']['name'])
                notebook_relpath = unquote(session['notebook']['path'])
                return Path(nbserver_root_dir, notebook_relpath)


def cleanup_project_dir_atexit(dirpath):
    """
    TODO: add docstring -- IPython kernel stores internal references to
     objects, so finalizer method isn't called on kernel shutdown. This
     handles that. Function outside class so atexit registry doesn't
     store reference to instance unnecessarily for whole session
    """
    if dirpath.is_dir() and next(dirpath.iterdir(), None) is None:
        try:
            dirpath.rmdir()
        except OSError:
            pass


def prune_projects():
    """delete (auto-named) projects for which a notebook doesn't exist"""


def prune_project(proj):
    """delete a single project by its name"""


def use_default_project():
    """
    TODO: add docstring -- use the default project for the current
     notebook
    """
    nb_path = get_notebook_path()
    default_project = Project(nb_path)
    config.project = default_project
