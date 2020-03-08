# -*- coding: utf-8 -*-

"""
OBGP: Open Book Genome Project
"""

import codecs
import os
import re
import setuptools

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """Taken from pypa pip setup.py:
    intentionally *not* adding an encoding option to open, See:
    https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    """
    return codecs.open(os.path.join(here, *parts), 'r').read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

def requirements():
    """Returns requirements.txt as a list usable by setuptools"""
    import os
    reqtxt = os.path.join(here, u'requirements.txt')
    with open(reqtxt) as f:
        return f.read().split()
                            
setuptools.setup(
    name='obgp',
    version=find_version("bgp", "__init__.py"),
    description="Open Book Genome Project",
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    author='OBGP',
    author_email='michael.karpeles@gmail.com',
    url='https://github.com/Open-Book-Genome-Project/sequencer',
    packages=[
        'bgp',
        'bgp/modules'
        ],
    keywords="open book genome analysis fulltext",
    platforms='any',
    include_package_data=True,
    license='LICENSE',
    install_requires=requirements(),
    classifiers=[
        "License :: OSI Approved :: MIT License",
        ],
    extras_require={
        ':python_version=="2.7"': ['argparse']
        }
)
