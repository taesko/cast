#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Note: To use the 'upload' functionality of this file, you must:
#   $ pip install twine

import io
import os
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command

# Package meta-data.
NAME = 'cast'
DESCRIPTION = 'FIle System Templates'
URL = 'https://github.com/taesko/cast'
EMAIL = 'taeskow@gmail.com'
AUTHOR = 'Antonio Todorov'

# What packages are required for this module to be executed?
REQUIRED = [
    'click'
]

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.rst' is present in your MANIFEST.in file!
with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()
try:
    import pypandoc

    long_description = pypandoc.convert(source=long_description, to='rst', format='markdown_github')
except Exception:
    print("warning - unable to convert markdown README to restructured text.")

# Load the package's __version__.py module as a dictionary.
about = {}
with open(os.path.join(here, NAME, '__version__.py')) as f:
    exec(f.read(), about)


class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel'.format(sys.executable))

        self.status('Uploading the package to PyPi via Twine…')
        os.system('twine upload dist/*')

        sys.exit()


class TestUploadCommand(Command):
    """Support setup.py test_upload."""

    description = 'Build and publish the package to TestPyPI.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel distribution…')
        os.system('{0} setup.py sdist bdist_wheel'.format(sys.executable))

        self.status('Uploading the package to PyPi via Twine…')
        os.system('twine upload --repository-url https://test.pypi.org/legacy/ dist/*')

        sys.exit()


# Where the magic happens:
setup(
    name='fs' + NAME,  # 'cast' already exists in PyPI
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    packages=find_packages(exclude=('tests',)),
    tests_require=['pytest', 'pytest-runner'],
    python_requires='>=3.6',
    # If your package is a single module, use this instead of 'packages':
    # py_modules=['mypackage'],

    entry_points={
        'console_scripts': ['cast=cast.cli:cli'],
    },
    install_requires=REQUIRED,
    include_package_data=True,
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Operating System :: POSIX :: Linux',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    # $ setup.py publish support.
    cmdclass={
        'upload': UploadCommand,
        'test_upload': TestUploadCommand
    },
)
