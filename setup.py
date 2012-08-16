import os

from setuptools import setup, find_packages, findall

PACKAGE_NAME = 'yawf'
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
REQUIREMENTS_FILEPATH = os.path.join(CURRENT_DIR, 'requirements', 'default.txt')
README_FILEPATH = os.path.join(CURRENT_DIR, 'README.rst')
VERSION_FILEPATH = os.path.join(CURRENT_DIR, PACKAGE_NAME, 'version.py')


def get_version():
    # populate namespace with __version__
    execfile(VERSION_FILEPATH)
    return locals()['__version__']


def get_requirements():
    with open(REQUIREMENTS_FILEPATH) as fp:
        return fp.read().splitlines()


def get_data_files():
    data_files = filter(
        lambda name: not name.endswith('.py') and not name.endswith('.pyc'),
        findall(PACKAGE_NAME))
    return [x.split(os.sep, 1)[-1] for x in data_files]


def get_long_description():
    return open(README_FILEPATH).read()


setup(
    name = PACKAGE_NAME,
    version = get_version(),
    packages = find_packages(CURRENT_DIR, exclude=('yawf_sample', 'yawf_sample.*')),
    package_data = {'': get_data_files()},

    # Metadata
    author = 'Nikolay Zakharov',
    author_email = 'nikolay@desh.su',
    url = 'https://github.com/freevoid/yawf',
    description = 'Yet Another Workflow Framework',
    long_description = get_long_description(),
    keywords = 'workflow state transition fsm django',
    install_requires = get_requirements(),
    license = 'MIT',
    classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Framework :: Django',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
    ],
)
