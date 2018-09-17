from __future__ import print_function
import sys

try:
    from setuptools import setup
except ImportError:
    print("libestg3b needs setuptools.", file=sys.stderr)
    print("Please install it using your package-manager or pip.", file=sys.stderr)
    sys.exit(1)

setup(
    name='libestg3b',
    version='0.0.1',
    description='',
    author='uberspace.de',
    author_email='hallo@uberspace.de',
    url='https://github.com/uberspace/libestg3b',
    packages=[
        'libestg3b',
    ],
    install_requires=[
        'holidays',
        'pytz',
        'python-dateutil',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Topic :: Office/Business :: Financial',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    zip_safe=True,
)
