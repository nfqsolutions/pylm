#!/usr/bin/env python

from setuptools import setup

with open('pylm/version.py') as f:
    exec(f.read())

setup(name='pylm',
      version=__version__,
      description='A framework to build clusters of high performance microservices',
      author='Guillem Borrell',
      author_email='guillemborrell@gmail.com',
      packages=['pylm',
                'pylm.components',
                'pylm.persistence',
                'pylm.standalone',
                'pylm.chained',
                'pylm.pipelined'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
          'Topic :: System :: Distributed Computing'
      ],
      install_requires=['protobuf>=3.0.0', 'requests', 'pyzmq', 'requests']
      )
