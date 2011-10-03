import os

from setuptools import setup, find_packages, findall

PACKAGE_ROOT = '.'
PACKAGE_NAME = 'yawf'

# populate namespace with __version__
execfile(os.path.join(PACKAGE_ROOT, PACKAGE_NAME, 'version.py'))

root_dir = os.path.abspath(os.path.dirname(__file__))

data_files = filter(
    lambda name: not name.endswith('.py') and not name.endswith('.pyc'),
    findall('yawf'))
data_files = [x.split(os.sep, 2)[-1] for x in data_files]

setup(
    name = PACKAGE_NAME,
    version = __version__,
    package_dir = {'': PACKAGE_ROOT},
    packages = find_packages(PACKAGE_ROOT, exclude=('yawf_sample', 'yawf_sample.*')),
    package_data = {'': data_files},

    # Metadata
    author = "Nikolay Zakharov",
    author_email = "nikolay@desh.su",
    keywords = "workflow state transition fsm django",
)
