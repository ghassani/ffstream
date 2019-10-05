import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from ffstream.version import Version


class PyTest(TestCommand):
    def initialize_options(self):
        super().initialize_options()
        self.test_suite = True
        self.test_args.append([
            'tests/playlist.py',
        ])

    def run_tests(self):
        import pytest
        sys.exit(pytest.main(self.test_args))

setup(
    name='ffstream',
    version=Version.STRING,
    license=open('LICENSE').read().strip(),
    author='Gassan Idriss',
    url='https://www.github.com/ghassani',
    description='',
    long_description=open('README.md').read().strip(),
    packages=find_packages(exclude=['tests']),
    py_modules=['ffstream'],
    install_requires=['ffmpeg-python', 'Pillow'],
    zip_safe=False,
    keywords='streaming ffmpeg linux',
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
)