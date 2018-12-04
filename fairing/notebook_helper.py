from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import json
import os.path
import re
import ipykernel
import requests
from fairing.utils import generate_context_tarball
import subprocess
from requests.compat import urljoin

DEFAULT_CONVERTED_FILENAME="app.py"

def is_in_notebook():
    try:
        ipykernel.get_connection_info()
    except RuntimeError:
        return False
    return True

def export_notebook_to_tar_gz(notebook_file, output_filename, converted_filename=DEFAULT_CONVERTED_FILENAME):
    subprocess.run(["jupyter", "nbconvert", "--to", "python", "--output", converted_filename, notebook_file])
    generate_context_tarball(converted_filename, output_filename)
