Introduction
============

``file-metadata`` is a python package that aims to analyze files and find
metadata that can be used from it.

Installation
============

Before installing file-metadata, a few dependencies need to be
installed. For Ubuntu, these can be installed with::

    $ sudo apt-get install perl openjdk-7-jre python-dev pkg-config libfreetype6-dev libpng12-dev liblapack-dev libblas-dev gfortran cmake libboost-python-dev libzbar-dev

Next, use ``pip`` to install the library. To install the latest stable
version, use::

    $ pip install file-metadata

To get development builds from the master branch of the github repo, use::

    $ pip install --pre file-metadata

Usage
=====

To use the package, you first need a file which can be any media file.

Let us first download an example qrcode from commons wikimedia::

    $ wget https://upload.wikimedia.org/wikipedia/commons/5/5b/Qrcode_wikipedia.jpg -O qrcode.jpg

And now, let us create a File object from this::

    >>> from file_metadata.generic_file import GenericFile
    >>> qr = GenericFile.create('qrcode.jpg')

Notice that when creating the file, the class automatically finds the best
type of class to analyze the file. In this case, it auto detecs that the
file is an image file, and uses the ``ImageFile`` class::

    >>> qr.__class__.__name__
    'ImageFile'

Now, to find possible analysis routines supported for the file, ``help(qr)``
can be checked. All routines beginning with ``analyze_`` perform analysis.
As the example we have is a qrcode, let us use ``analyze_barcode_zxing()``::

    >>> qr.analyze_barcode_zxing()
    {'zxing:Barcodes': [{'data': 'http://www.wikipedia.com',
       'format': 'QR_CODE',
       'points': [(50.0, 316.0), (50.0, 52.0), (314.0, 52.0), (278.0, 280.0)],
       'raw_data': 'http://www.wikipedia.com'}]}

Which tells us the bounding box of the barcode (``points``) and also the data
(``http://www.wikipedia.com``). It also mentions that the format of the barcode
is QR_CODE.

Similarly, to check the mimetype, the analysis routing ``analyze_mimetype()``
can be used::

    >>> qr.analyze_mimetype()
    {'File:MIMEType': 'image/jpeg'}

To perform all the analyze routines on the image, the
``analyze()`` method can be used. It runs all the analysis routines on the
file and gives back the merged result::

    >>> qr.analyze()
 
Development
===========

Testing
-------

To test the code, install dependencies using::

    $ pip install -r test-requirements.txt

and then execute::

    $ python -m pytest

Docker
------

To pull the ``latest`` docker image use::

    $ docker pull pywikibotcatfiles/docker-file-metadata

Supported tags and respective ``Dockerfile`` links:
 * ``latest``, ``ubuntu-14.04`` (`docker/Dockerfile <https://github.com/pywikibot-catfiles/docker-file-metadata/blob/master/Dockerfile.ubuntu>`__)
 * ``ubuntu-16.04`` (`docker/Dockerfile <https://github.com/pywikibot-catfiles/docker-file-metadata/blob/master/Dockerfile.ubuntu-16.04>`__)
 * ``centos-7`` (`docker/Dockerfile <https://github.com/pywikibot-catfiles/docker-file-metadata/blob/master/Dockerfile.centos>`__)

For more information about this image and its history, please see `the Build
Details <https://hub.docker.com/r/pywikibotcatfiles/docker-file-metadata/builds/>`__
(``pywikibotcatfiles/docker-file-metadata``). This image is updated via push
to the ``pywikibot-catfiles/docker-file-metadata``
`GitHub repo <https://github.com/pywikibot-catfiles/docker-file-metadata>`__
or the ``pywikibot-catfiles/file-metadata``
`GitHub repo <https://github.com/pywikibot-catfiles/file-metadata>`__ (by
DockerHub link `to image <https://hub.docker.com/r/pywikibotcatfiles/file-metadata/builds/>`__
``pywikibotcatfiles/file-metadata``).

Build status
------------

.. image:: https://travis-ci.org/AbdealiJK/file-metadata.svg?branch=master
   :target: https://travis-ci.org/AbdealiJK/file-metadata

.. image:: https://codecov.io/gh/AbdealiJK/file-metadata/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/AbdealiJK/file-metadata

`:whale:(docker) <https://hub.docker.com/r/pywikibotcatfiles/docker-file-metadata/builds/>`__

Credits
-------

This package has been derived from
`pywikibot-compat <https://gerrit.wikimedia.org/r/#/admin/projects/pywikibot/compat>`__.
Specifically, the script ``catimages.py`` which can be found at
`pywikibot-compat/catimages.py <https://phabricator.wikimedia.org/diffusion/PWBO/browse/master/catimages.py>`__.
These packages were created by `DrTrigon <mailto:dr.trigon@surfeu.ch>`__ who
is the original author of this package.

LICENSE
=======

.. image:: https://img.shields.io/github/license/AbdealiJK/file-metadata.svg
   :target: https://opensource.org/licenses/MIT

This code falls under the
`MIT License <https://tldrlegal.com/license/mit-license>`__.
Please note that some files or content may be copied from other places
and have their own licenses. Dependencies that are being used to generate
the databases also have their own licenses.
