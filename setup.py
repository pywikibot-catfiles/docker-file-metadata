#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import sys
from distutils import log
from distutils.errors import DistutilsSetupError

import setupdeps

log.set_verbosity(log.INFO)

setup_deps = [
    setupdeps.Distro(),
    setupdeps.SetupTools()
]

install_deps = [
    # Core deps
    setupdeps.LibMagic(),
    setupdeps.PythonMagic(),
    setupdeps.Six(),
    setupdeps.ExifTool(),
    setupdeps.AppDirs(),
    # Image deps
    setupdeps.PathLib(),
    setupdeps.Pillow(),
    setupdeps.Numpy(),
    setupdeps.Dlib(),
    setupdeps.ScikitImage(),
    setupdeps.MagickWand(),
    setupdeps.Wand(),
    setupdeps.LibZBar(),
    setupdeps.ZBar(),
    setupdeps.JavaJRE(),
    setupdeps.ZXing(),
    setupdeps.PyColorName(),
    # Audio video deps
    setupdeps.FFProbe(),
]


def check_deps(deplist):
    failed_deps = []
    for dep in deplist:
        try:
            log_msg = dep.check()
            log.info(dep.name + ' - ' + log_msg)
        except setupdeps.CheckFailed as err:
            log.info(dep.name + ' - ' + err.args[0])
            failed_deps.append(dep)

    if len(failed_deps) > 0:
        msg = 'Some dependencies could not be installed automatically: '
        msg += ", ".join(i.name for i in failed_deps)
        for dep in failed_deps:
            install_msg = dep.install_help_msg()
            if install_msg:
                msg += '\n* ' + install_msg
        raise DistutilsSetupError(msg)
    return deplist


def get_install_requires(deplist):
    packages = []
    for dep in check_deps(deplist):
        packages += dep.get_install_requires()
    return packages


def read_reqs(reqs_filename):
    reqs = open(reqs_filename).read().strip().splitlines()
    return list(i for i in reqs if not (i.startswith('#') or len(i) == 0))


if __name__ == '__main__':
    log.info('Check and install dependencies required for setup:')
    setup_packages = []
    for dep in check_deps(setup_deps):
        setup_packages += dep.get_setup_requires()

    if setup_packages:
        log.info('Some required packages required for file-metadata\'s setup '
                 'were not found: {0}.\nInstalling them with `pip` ...'
                 .format(", ".join(setup_packages)))
        out = setupdeps.setup_install(setup_packages)
        if out is not True:
            raise DistutilsSetupError(
                'Unable to install package(s) required by the setup script '
                'using pip: {0}\nReport this issue to the maintainer.\n'
                'Temporarily, this could be solved by running: '
                '`python -m pip install {1}`.'
                .format(", ".join(setup_packages), " ".join(setup_packages)))

    log.info('Check dependencies required for using file-metadata:')
    install_required = get_install_requires(install_deps)

    log.info('Downloading 3rd party data files:')
    for dep in install_deps:
        data_msg = dep.get_data_files()
        if data_msg:
            log.info(dep.name + ' - ' + data_msg)

    test_required = read_reqs('test-requirements.txt')
    VERSION = open(os.path.join('file_metadata', 'VERSION')).read().strip()

    if sys.version_info >= (3,):  # mock is not required for python 3
        test_required.remove('mock')

    from setuptools import find_packages, setup

    setup(name='file-metadata',
          version=VERSION,
          description='Helps to find structured metadata from a given file.',
          author="DrTrigon",
          author_email="dr.trigon@surfeu.ch",
          maintainer="AbdealiJK",
          maintainer_email='abdealikothari@gmail.com',
          license="MIT",
          url='https://github.com/AbdealiJK/file-metadata',
          packages=find_packages(exclude=["build.*", "tests.*", "tests"]),
          # Dependency management by pip
          install_requires=install_required,
          tests_require=test_required,
          # Setuptools has a bug where they use isinstance(x, str) instead
          # of basestring. Because of this we convert it to str for Py2.
          package_data={str('file_metadata'): [str("VERSION"),
                                               str("datafiles/*")]},
          entry_points={
              "console_scripts": [
                  "wikibot-filemeta-simple = "
                  "file_metadata.wikibot.simple_bot:main",
                  "wikibot-create-config = "
                  "file_metadata.wikibot.generate_user_files:main"]},
          # from http://pypi.python.org/pypi?%3Aaction=list_classifiers
          classifiers=[
              'Development Status :: 4 - Beta',
              'Environment :: Console',
              'Environment :: MacOS X',
              'Environment :: Win32 (MS Windows)',
              'Intended Audience :: Developers',
              'Operating System :: OS Independent',
              'Programming Language :: Python :: Implementation :: CPython'])
