#!/usr/bin/env python

from setuptools import setup

__version__ = None
with open('pylm/__init__.py') as f:
    exec(f.read())


long_description = """
Pylm
====

Pylm is the Python implementation of PALM, a framework to build
clusters of high performance components. It is presented in two
different levels of abstraction. In the high level API you will find
servers and clients that are functional *out of the box*. Use the high
level API if you are interested in simple communication patterns like
client-server, master-slave or a streaming pipeline. In the low level
API there are a variety of small components that, once combined,
they can be used to implement almost any kind of
component. It's what the high level API uses under the hood. Choose
the low level API if you are interested in creating your custom
component and your custom communication pattern.

**Pylm requires a version of Python equal or higher than 3.4, and it is
more thoroughly tested with Python 3.5.**

Installing **pylm** is as easy as:

.. code-block:: bash

   $> pip install pylm

* `PYPI package page <https://pypi.python.org/pypi/pylm/>`_

* `Documentation <http://pylm.readthedocs.io/en/latest/>`_

* `Source code <https://github.com/nfqsolutions/pylm>`_

Pylm is released under a dual licensing scheme. The source is released
as-is under the the AGPL version 3 license, a copy of the license is
included with the source. If this license does not suit you,
you can purchase a commercial license from `NFQ Solutions
<http://nfqsolutions.com>`_

This project has been funded by the Spanish Ministry of Economy and
Competitivity under the grant IDI-20150936, cofinanced with FEDER
funds.
"""
    
setup(name='pylm',
      version=__version__,
      description='A framework to build clusters of high performance components',
      long_description=long_description,
      author='Guillem Borrell',
      author_email='guillemborrell@gmail.com',
      packages=['pylm',
                'pylm.parts',
                'pylm.persistence',
                'pylm.remote'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: System :: Distributed Computing',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'License :: OSI Approved :: GNU Affero General Public License v3'
      ],
      setup_requires=['pytest-runner'],
      install_requires=['protobuf>=3.0.0', 'requests', 'pyzmq']
      )
