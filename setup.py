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

with open("bgp/__init__.py", "r", encoding="utf-8") as fh:
    version_file = fh.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")


setuptools.setup(
    name='obgp',
    version=version,
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
