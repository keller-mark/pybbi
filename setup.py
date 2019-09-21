#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext as _build_ext
from subprocess import check_call
from distutils import log
import os.path as op
import glob
import sys
import os
import re
import io


thisdir = op.dirname(op.realpath(__file__))


class lazylist(list):
    '''
    Used to delay the build-time Cython and numpy imports required to configure
    our list of extension modules until after setup_requires has been processed.

    '''
    def __init__(self, callback):
        self._list = None
        self.callback = callback

    def _cached_list(self):
        if self._list is None:
            self._list = self.callback()
        return self._list

    def __len__(self):
        return len(self._cached_list())

    def __iter__(self):
        for e in self._cached_list():
            yield e

    def __getitem__(self, i):
        return self._cached_list()[i]


def read(*parts, **kwargs):
    encoding = kwargs.pop('encoding', 'utf-8')
    filepath = op.join(op.dirname(__file__), *parts)
    return io.open(filepath, encoding=encoding).read()


def get_version(pkg):
    version = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
        read(pkg, '__init__.py'),
        re.MULTILINE).group(1)
    return version


# Paths to propagate to make
extra_library_dirs = [op.join(sys.prefix, 'lib')]
extra_include_dirs = [op.join(sys.prefix, 'include')]


# OpenSSL
inc_dirs = [
    op.join(sys.prefix, 'include', 'openssl'),
    '/usr/include/openssl',
]
for inc_dir in inc_dirs:
    if op.isdir(inc_dir):
        extra_include_dirs.append(inc_dir)
        break
if sys.platform == "darwin":
    # https://solitum.net/openssl-os-x-el-capitan-and-brew/
    lib_dir = '/usr/local/opt/openssl/lib'
    if op.isdir(lib_dir):
        extra_library_dirs.append(lib_dir)
    inc_dir = '/usr/local/opt/openssl/include'
    if op.isdir(inc_dir):
        extra_include_dirs.append(inc_dir)


# libPNG
inc_dirs = glob.glob(op.join(sys.prefix, 'include', 'libpng*'))
for inc_dir in inc_dirs:
    if op.isdir(inc_dir):
        extra_include_dirs.append(inc_dir)
        break
if sys.platform == "darwin":
    inc_dirs = glob.glob('/usr/local/include/libpng*')
    for inc_dir in inc_dirs:
        if op.isdir(inc_dir):
            extra_include_dirs.append(inc_dir)


class build_ext(_build_ext):
    def run(self):
        os.environ['SETUP_PY'] = '1'
        for lib_dir in extra_library_dirs[::-1]:
            os.environ["LIBRARY_PATH"] = \
                lib_dir + ':' + os.environ.get("LIBRARY_PATH", "")
        for inc_dir in extra_include_dirs[::-1]:
            os.environ["C_INCLUDE_PATH"] = \
                inc_dir + ':' + os.environ.get("C_INCLUDE_PATH", "")

        # First, compile our C library: libkent.a
        log.info("LIBRARY_PATH: " + os.environ.get("LIBRARY_PATH", ""))
        log.info("C_INCLUDE_PATH: " + os.environ.get("C_INCLUDE_PATH", ""))
        log.info("Compiling libkent archive...")
        check_call(['make', 'build-ucsc'])

        # Now, proceed to build extension modules
        log.info("Building extension module...")
        _build_ext.run(self)


def get_ext_modules():
    from Cython.Build import cythonize
    import numpy

    ext_modules = [
        Extension(
            name='bbi.cbbi',
            sources=[
                op.join(thisdir, 'bbi/cbbi.pyx')
            ],
            library_dirs=[
                op.join(thisdir, 'src/x86_64'),
                op.join(thisdir, 'htslib'),
            ] + extra_library_dirs,
            libraries=[
                'c', 'z', 'pthread', 'ssl', 'crypto', 'kent', 'hts',
            ],
            include_dirs=[
                numpy.get_include(),
                op.join(thisdir, 'include'),
                op.join(thisdir, 'htslib'),
            ] + extra_include_dirs,
        ),
    ]
    return cythonize(ext_modules)


setup(
    name='pybbi',
    author='Nezar Abdennur',
    author_email='nabdennur@gmail.com',
    license='MIT',
    version=get_version('bbi'),
    packages=['bbi'],
    description='Python bindings to UCSC Big Binary (bigWig/bigBed) file library',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/nvictus/pybbi',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],
    zip_safe=False,
    setup_requires=[
        'setuptools>=18.0',
        'cython',
        'numpy',
    ],
    install_requires=[
        'six',
        'numpy'
    ],
    tests_require=[
        'pytest'
    ],
    ext_modules=lazylist(get_ext_modules),
    cmdclass={
        'build_ext': build_ext
    }
)
