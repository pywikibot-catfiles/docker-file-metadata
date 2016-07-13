# -*- coding: utf-8 -*-
"""
Various dependencies that are required for file-metadata which need some
special handling.
"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import ctypes.util
import hashlib
import os
import subprocess
import sys
from distutils import sysconfig

try:
    from urllib.request import urlopen
except ImportError:  # Python 2
    from urllib2 import urlopen


PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))


def data_path():
    name = os.path.join(PROJECT_PATH, 'file_metadata', 'datafiles')
    if not os.path.exists(name):
        os.makedirs(name)
    return name


def which(cmd):
    try:
        from shutil import which
        return which(cmd)
    except ImportError:  # For python 3.2 and lower
        try:
            output = subprocess.check_output(["which", cmd],
                                             stderr=subprocess.STDOUT)
        except (OSError, subprocess.CalledProcessError):
            return None
        else:
            output = output.decode(sys.getfilesystemencoding())
            return output.strip()


def setup_install(packages):
    """
    Install packages using pip to the current folder. Useful to import
    packages during setup itself.
    """
    packages = list(packages)
    if not packages:
        return True
    try:
        subprocess.call([sys.executable, "-m", "pip", "install",
                         "-t", PROJECT_PATH] + packages)
        return True
    except subprocess.CalledProcessError:
        return False


def download(url, filename, overwrite=False, sha1=None):
    """
    Download the given URL to the given filename. If the file exists,
    it won't be downloaded unless asked to overwrite. Both, text data
    like html, txt, etc. or binary data like images, audio, etc. are
    acceptable.

    :param url:       A URL to download.
    :param filename:  The file to store the downloaded file to.
    :param overwrite: Set to True if the file should be downloaded even if it
                      already exists.
    :param sha1:      The sha1 checksum to verify the file using.
    """
    blocksize = 16 * 1024
    _hash = hashlib.sha1()
    if os.path.exists(filename) and not overwrite:
        # Do a pass for the hash if it already exists
        with open(filename, "rb") as downloaded_file:
            while True:
                block = downloaded_file.read(blocksize)
                if not block:
                    break
                _hash.update(block)
    else:
        # If it doesn't exist, or overwrite=True, find hash while downloading
        response = urlopen(url)
        with open(filename, 'wb') as out_file:
            while True:
                block = response.read(blocksize)
                if not block:
                    break
                out_file.write(block)
                _hash.update(block)
    return _hash.hexdigest() == sha1


class CheckFailed(Exception):
    """
    Exception thrown when a ``SetupPackage.check()`` fails.
    """
    pass


class PkgConfig(object):
    """
    This is a class for communicating with pkg-config.
    """
    def __init__(self):
        if sys.platform == 'win32':
            self.has_pkgconfig = False
        else:
            self.pkg_config = os.environ.get('PKG_CONFIG', 'pkg-config')
            self.set_pkgconfig_path()

            try:
                with open(os.devnull) as nul:
                    subprocess.check_call([self.pkg_config, "--help"],
                                          stdout=nul, stderr=nul)
                self.has_pkgconfig = True
            except (subprocess.CalledProcessError, OSError):
                self.has_pkgconfig = False
                print("IMPORTANT WARNING: pkg-config is not installed.")
                print("file-metadata may not be able to find some of "
                      "its dependencies.")

    def set_pkgconfig_path(self):
        pkgconfig_path = sysconfig.get_config_var('LIBDIR')
        if pkgconfig_path is None:
            return

        pkgconfig_path = os.path.join(pkgconfig_path, 'pkgconfig')
        if not os.path.isdir(pkgconfig_path):
            return

        os.environ['PKG_CONFIG_PATH'] = ':'.join(
            [os.environ.get('PKG_CONFIG_PATH', ""), pkgconfig_path])

    def get_version(self, package):
        """
        Get the version of the package from pkg-config.
        """
        if not self.has_pkgconfig:
            return None

        try:
            output = subprocess.check_output(
                [self.pkg_config, package, "--modversion"],
                stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            return None
        else:
            output = output.decode(sys.getfilesystemencoding())
            return output.strip()


# The PkgConfig class should be used through this singleton
pkg_config = PkgConfig()


class SetupPackage(object):
    name = None
    optional = False
    pkg_names = {
        "apt-get": None,
        "yum": None,
        "dnf": None,
        "pacman": None,
        "zypper": None,
        "brew": None,
        "port": None,
        "windows_url": None
    }

    def check(self):
        """
        Check whether the dependencies are met. Should raise a ``CheckFailed``
        exception if the dependency was not found.
        """
        pass

    def get_install_requires(self):
        """
        Return a list of Python packages that are required by the package.
        pip / easy_install will attempt to download and install this
        package if it is not installed.
        """
        return []

    def get_setup_requires(self):
        """
        Return a list of Python packages that are required by the setup.py
        itself. pip / easy_install will attempt to download and install this
        package if it is not installed on top of the setup.py script.
        """
        return []

    def get_data_files(self):
        """
        Perform required actions to add the data files into the directory
        given by ``data_path()``.
        """
        pass

    def install_help_msg(self):
        """
        The help message to show if the package is not installed. The help
        message shown depends on whether some class variables are present.
        """
        def _try_managers(*managers):
            for manager in managers:
                pkg_name = self.pkg_names.get(manager, None)
                if pkg_name and which(manager) is not None:
                    pkg_note = None
                    if isinstance(pkg_name, (tuple, list)):
                        pkg_name, pkg_note = pkg_name
                    msg = ('Try installing {0} with `{1} install {2}`.'
                           .format(self.name, manager, pkg_name))
                    if pkg_note:
                        msg += ' Note: ' + pkg_note
                    return msg

        message = None
        if sys.platform == "win32":
            url = self.pkg_names.get("windows_url", None)
            if url:
                return ('Please check {0} for instructions to install {1}'
                        .format(url, self.name))
        elif sys.platform == "darwin":
            manager_message = _try_managers("brew", "port")
            return manager_message or message
        elif sys.platform.startswith("linux"):
            try:
                import distro
            except ImportError:
                setup_install(['distro'])
                import distro
            release = distro.id()
            if release in ('debian', 'ubuntu', 'linuxmint', 'raspbian'):
                manager_message = _try_managers('apt-get')
                if manager_message:
                    return manager_message
            elif release in ('centos', 'rhel', 'redhat', 'fedora',
                             'scientific', 'amazon', ):
                manager_message = _try_managers('dnf', 'yum')
                if manager_message:
                    return manager_message
            elif release in ('sles', 'opensuse'):
                manager_message = _try_managers('zypper')
                if manager_message:
                    return manager_message
            elif release in ('arch'):
                manager_message = _try_managers('pacman')
                if manager_message:
                    return manager_message
        return message


class Distro(SetupPackage):
    name = "distro"

    def check(self):
        return 'Will be installed with pip.'

    def get_setup_requires(self):
        try:
            import distro  # noqa (unused import)
            return []
        except ImportError:
            return ['distro']


class SetupTools(SetupPackage):
    name = 'setuptools'

    def check(self):
        return 'Will be installed with pip.'

    def get_setup_requires(self):
        try:
            import setuptools  # noqa (unused import)
            return []
        except ImportError:
            return ['setuptools']


class PathLib(SetupPackage):
    name = 'pathlib'

    def check(self):
        if sys.version_info < (3, 4):
            return 'Backported pathlib2 will be installed with pip.'
        else:
            return 'Already installed in python 3.4+'

    def get_install_requires(self):
        if sys.version_info < (3, 4):
            return ['pathlib2']
        else:
            return []


class AppDirs(SetupPackage):
    name = 'appdirs'

    def check(self):
        return 'Will be installed with pip.'

    def get_install_requires(self):
        return ['appdirs']


class LibMagic(SetupPackage):
    name = 'libmagic'
    pkg_names = {
        "apt-get": 'libmagic-dev',
        "yum": 'file',
        "dnf": 'file',
        "pacman": None,
        "zypper": None,
        "brew": 'libmagic',
        "port": None,
        "windows_url": None
    }

    def check(self):
        file_path = which('file')
        if file_path is None:
            raise CheckFailed('Needs to be installed manually.')
        else:
            return 'Found "file" utility at {0}.'.format(file_path)


class PythonMagic(SetupPackage):
    name = 'python-magic'

    def check(self):
        return 'Will be installed with pip.'

    def get_install_requires(self):
        return ['python-magic']


class Six(SetupPackage):
    name = 'six'

    def check(self):
        return 'Will be installed with pip.'

    def get_install_requires(self):
        return ['six>=1.8.0']


class ExifTool(SetupPackage):
    name = 'exiftool'
    pkg_names = {
        "apt-get": 'libimage-exiftool-perl',
        "yum": 'perl-Image-ExifTool',
        "dnf": 'perl-Image-ExifTool',
        "pacman": None,
        "zypper": None,
        "brew": 'exiftool',
        "port": 'p5-image-exiftool',
        "windows_url": 'http://www.sno.phy.queensu.ca/~phil/exiftool/'
    }

    def check(self):
        exiftool_path = which('exiftool')
        if exiftool_path is None:
            raise CheckFailed('Needs to be installed manually.')
        else:
            return 'Found at {0}.'.format(exiftool_path)


class Pillow(SetupPackage):
    name = 'pillow'

    def check(self):
        return 'Will be installed with pip.'

    def get_install_requires(self):
        return ['pillow>=2.5.0']


class Numpy(SetupPackage):
    name = 'numpy'

    def check(self):
        return 'Will be installed with pip.'

    def get_install_requires(self):
        return ['numpy>=1.7.2']


class Dlib(SetupPackage):
    name = 'dlib'

    def check(self):
        return 'Will be installed with pip.'

    def get_install_requires(self):
        return ['dlib']


class ScikitImage(SetupPackage):
    name = 'scikit-image'

    def check(self):
        return 'Will be installed with pip.'

    def get_install_requires(self):
        # For some reason some dependencies of scikit-image aren't installed
        # by pip: https://github.com/scikit-image/scikit-image/issues/2155
        return ['scipy', 'matplotlib', 'scikit-image>=0.12']


class MagickWand(SetupPackage):
    name = 'magickwand'
    pkg_names = {
        "apt-get": 'libmagickwand-dev',
        "yum": 'ImageMagick-devel',
        "dnf": 'ImageMagick-devel',
        "pacman": None,
        "zypper": None,
        "brew": 'imagemagick',
        "port": 'imagemagick',
        "windows_url": ("http://docs.wand-py.org/en/latest/guide/"
                        "install.html#install-imagemagick-on-windows")
    }

    def check(self):
        # `wand` already checks for magickwand, but only when importing, not
        # during installation. See https://github.com/dahlia/wand/issues/293
        magick_wand = pkg_config.get_version("MagickWand")
        if magick_wand is None:
            raise CheckFailed('Needs to be installed manually.')
        else:
            return 'Found with pkg-config.'


class Wand(SetupPackage):
    name = 'wand'

    def check(self):
        return 'Will be installed with pip.'

    def get_install_requires(self):
        return ['wand']


class PyColorName(SetupPackage):
    name = 'pycolorname'

    def check(self):
        return 'Will be installed with pip.'

    def get_install_requires(self):
        return ['pycolorname']


class LibZBar(SetupPackage):
    name = 'libzbar'
    pkg_names = {
        "apt-get": 'libzbar-dev',
        "yum": 'zbar-devel',
        "dnf": 'zbar-devel',
        "pacman": None,
        "zypper": None,
        "brew": 'zbar',
        "port": None,
        "windows_url": None
    }

    def check(self):
        libzbar = ctypes.util.find_library('zbar')
        if libzbar is None:
            raise CheckFailed('Needs to be installed manually.')
        else:
            return 'Found {0}.'.format(libzbar)


class ZBar(SetupPackage):
    name = 'zbar'

    def check(self):
        return 'Will be installed with pip.'

    def get_install_requires(self):
        return ['zbar']


class JavaJRE(SetupPackage):
    name = 'java'
    pkg_names = {
        "apt-get": 'openjdk-7-jre',
        "yum": 'java',
        "dnf": 'java',
        "pacman": None,
        "zypper": None,
        "brew": None,
        "port": None,
        "windows_url": "https://java.com/download/"
    }

    def check(self):
        java_path = which('java')
        if java_path is None:
            raise CheckFailed('Needs to be installed manually.')
        else:
            return 'Found at {0}.'.format(java_path)


class ZXing(SetupPackage):
    name = 'zxing'

    def check(self):
        return 'Will be downloaded from their maven repositories.'

    @staticmethod
    def download_jar(data_folder, path, name, ver, **kwargs):
        data = {'name': name, 'ver': ver, 'path': path}
        fname = os.path.join(data_folder, '{name}-{ver}.jar'.format(**data))
        url = ('http://central.maven.org/maven2/{path}/{name}/{ver}/'
               '{name}-{ver}.jar'.format(**data))
        download(url, fname, **kwargs)
        return fname

    def get_data_files(self):
        msg = 'Unable to download "{0}" correctly.'
        if not self.download_jar(
                data_path(), 'com/google/zxing', 'core', '3.2.1',
                sha1='2287494d4f5f9f3a9a2bb6980e3f32053721b315'):
            return msg.format('zxing-core')
        if not self.download_jar(
                data_path(), 'com/google/zxing', 'javase', '3.2.1',
                sha1='78e98099b87b4737203af1fcfb514954c4f479d9'):
            return msg.format('zxing-javase')
        if not self.download_jar(
                data_path(), 'com/beust', 'jcommander', '1.48',
                sha1='bfcb96281ea3b59d626704f74bc6d625ff51cbce'):
            return msg.format('jcommander')
        return 'Successfully downloaded zxing-javase, zxing-core, jcommander.'


class FFProbe(SetupPackage):
    name = 'ffprobe'
    pkg_names = {
        "apt-get": 'libav-tools',
        "yum": ('ffmpeg', 'This requires the RPMFusion repo to be enabled.'),
        "dnf": ('ffmpeg', 'This requires the RPMFusion repo to be enabled.'),
        "pacman": None,
        "zypper": None,
        "brew": 'ffmpeg',
        "port": None,
        "windows_url": None
    }

    def check(self):
        ffprobe_path = which('ffprobe') or which('avprobe')
        if ffprobe_path is None:
            raise CheckFailed('Needs to be installed manually.')
        else:
            return 'Found at {0}.'.format(ffprobe_path)
