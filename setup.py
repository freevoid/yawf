import os

from setuptools import setup, find_packages

PACKAGE_ROOT = 'src'
PACKAGE_NAME = 'yawf'

# populate namespace with __version__
execfile(os.path.join(PACKAGE_ROOT, PACKAGE_NAME, 'version.py'))

root_dir = os.path.abspath(os.path.dirname(__file__))

setup(
    name = PACKAGE_NAME,
    version = __version__,
    package_dir = {'': PACKAGE_ROOT},
    packages = find_packages(PACKAGE_ROOT),

    # Metadata
    author = "Nikolay Zakharov",
    author_email = "nikolay@desh.su",
    keywords = "workflow state transition fsm django",
)
