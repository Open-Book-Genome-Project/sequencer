"""
OBGP: Open Book Genome Project
"""

import codecs
from os.path import dirname, isdir, join, abspath
import re
from subprocess import CalledProcessError, check_output
import setuptools

here = abspath(dirname(__file__))


def read(*parts):
    """Taken from pypa pip setup.py:
    intentionally *not* adding an encoding option to open, See:
    https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    """
    return codecs.open(join(here, *parts), 'r').read()

def get_version():
    # Source: https://github.com/Changaco/version.py
    PREFIX = ''
    tag_re = re.compile(r'\btag: %s([0-9][^,]*)\b' % PREFIX)
    version_re = re.compile('^Version: (.+)$', re.M)

    # Return the version if it has been injected into the file by git-archive
    version = tag_re.search('$Format:%D$')
    if version:
        return version.group(1)

    d = dirname(__file__)

    if isdir(join(d, '.git')):
        # Get the version using "git describe".
        cmd = 'git describe --tags --match %s[0-9]* --dirty --always' % PREFIX
        try:
            version = check_output(cmd.split()).decode().strip()[len(PREFIX):]
        except CalledProcessError:
            raise RuntimeError('Unable to get version number from git tags')

        # PEP 440 compatibility
        if '-' in version:
            if version.endswith('-dirty'):
                raise RuntimeError('The working tree is dirty')
            version = '.post'.join(version.split('-')[:2])

    else:
        # Extract the version from the PKG-INFO file.
        with open(join(d, 'PKG-INFO')) as f:
            version = version_re.search(f.read()).group(1)

    return version

def requirements():
    """Returns requirements.txt as a list usable by setuptools"""
    reqtxt = join(here, 'requirements.txt')
    with open(reqtxt) as f:
        return f.read().split()
                            
setuptools.setup(
    name='obgp',
    version=get_version(),
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
)
