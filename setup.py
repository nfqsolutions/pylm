#!/usr/bin/env python

from setuptools import setup

with open('pylm/version.py') as f:
    exec(f.read())

setup(name='pylm',
      version=__version__,
      description='A framework to build clusters of high performance components',
      author='Guillem Borrell',
      author_email='guillemborrell@gmail.com',
      packages=['pylm',
                'pylm.components',
                'pylm.persistence',
                'pylm.standalone',
                'pylm.chained',
                'pylm.pipelined',
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
          'License :: OSI Approved :: GNU Affero General Public License v3'
      ],
      install_requires=['protobuf>=3.0.0', 'requests', 'pyzmq', 'requests']
      )
