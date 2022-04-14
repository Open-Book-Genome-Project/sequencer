"""
OBGP: Open Book Genome Project
"""

import codecs
from os.path import dirname, isdir, join, abspath
import re
from subprocess import CalledProcessError, check_output
import setuptools

here = abspath(dirname(__file__))


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    install_requires = fh.read()
    print(install_requires)

setuptools.setup(
    name='obgp',
    version='0.0.35',
    description="Open Book Genome Project",
    long_description=long_description,
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
    install_requires=install_requires,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        ],
)
