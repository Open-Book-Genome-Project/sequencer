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
    version='0.0.36',
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
    keywords="open book genome fulltext analysis",
    platforms='any',
    include_package_data=True,
    license='https://www.gnu.org/licenses/agpl-3.0.en.html',
    install_requires=install_requires,
    classifiers=[
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        ],
)
