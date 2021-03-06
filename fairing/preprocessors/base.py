
from fairing.constants import constants
from fairing import utils

import os
import fairing
import tarfile
import glob
import logging


class BasePreProcessor(object):
    """
    Prepares a context that gets sent to the builder for the docker build and sets the entrypoint

    input_files -  the source files to be processed
    executable - the file to execute using command (e.g. main.py)
    output_map - a list of files to be added without preprocessing
    path_prefix - the prefix of the path where the files will be added in the container
    command - the command to pass to the builder

    """
    def __init__(
        self,
        input_files=[],
        command=["python"],
        executable=None,
        path_prefix=constants.DEFAULT_DEST_PREFIX,
        output_map=None
    ):
        self.executable = executable
        self.input_files = set(input_files)
        self.output_map = output_map if output_map else {}
        self.path_prefix = path_prefix
        self.command = command

        self.set_default_executable()

    def set_default_executable(self):
        if self.executable is not None:
            return self.executable
        if len(self.input_files) == 1:
            self.executable = list(self.input_files)[0]
            return
        python_files = [item for item in self.input_files if item.endswith(".py") and item is not '__init__.py']
        if len(python_files) == 1:
            self.executable = python_files[0]
            return

    def preprocess(self):
        return self.input_files

    def context_map(self):
        # Create context mapping from destination --> source to avoid duplicates
        # in context archive.
        c_map = {}
        for src, dst in self.fairing_runtime_files().items():
            if dst not in c_map:
                c_map[dst] = src
            else:
                logging.warning('{} already exists in Fairing context, skipping...'.format(src))

        for f in self.input_files:
            dst = os.path.join(self.path_prefix, f)
            if dst not in c_map:
                c_map[dst] = f
            else:
                logging.warning('{} already exists in Fairing context, skipping...'.format(f))

        for src, dst in self.output_map.items():
            if dst not in c_map:
                c_map[dst] = src
            else:
                logging.warning('{} already exists in Fairing context, skipping...'.format(src))

        return c_map

    def context_tar_gz(self, output_file=constants.DEFAULT_CONTEXT_FILENAME):
        self.input_files = self.preprocess()
        with tarfile.open(output_file, "w:gz", dereference=True) as tar:
            for dst, src in self.context_map().items():
                tar.add(src, filter=reset_tar_mtime, arcname=dst, recursive=False)
        self._context_tar_path = output_file
        return output_file, utils.crc(self._context_tar_path)

    def get_command(self):
        if self.command is None or self.executable is None:
            return []
        cmd = self.command.copy()
        cmd.append(os.path.join(self.path_prefix, self.executable))
        return cmd

    def fairing_runtime_files(self):
        fairing_dir = os.path.dirname(fairing.__file__)
        ret = {}
        for f in ["__init__.py", "runtime_config.py"]:
            ret[os.path.join(fairing_dir, f)] = os.path.join(self.path_prefix, "fairing", f)
        return ret

# Reset the mtime on the the tarball for reproducibility
def reset_tar_mtime(tarinfo):
    tarinfo.mtime = 0
    return tarinfo
