
import os
import setuptools

from lager import __version__ as lager_version

def readme():
    path = os.path.dirname(__file__)
    with open(os.path.join(path, 'README.md')) as f:
        return f.read()

name = 'lager-cli'
description = 'Lager Command Line Interface'
author = 'Lager Data LLC'
email = 'hello@lagerdata.com'
classifiers = [
    'Development Status :: 3 - Alpha',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Topic :: Software Development',
]

if __name__ == "__main__":
    setuptools.setup(
        name=name,
        version=lager_version,
        description=description,
        long_description=readme(),
        classifiers=classifiers,
        url='https://github.com/lagerdata/lager-cli',
        author=author,
        author_email=email,
        maintainer=author,
        maintainer_email=email,
        license='MIT',
        python_requires=">=3.6",
        packages=setuptools.find_packages(),
        install_requires='''
            async-generator == 1.10
            bson == 0.5.10
            certifi == 2020.4.5.1
            chardet == 3.0.4
            click == 7.1.2
            colorama == 0.4.3
            h11 == 0.9.0
            idna == 2.9
            ipaddress == 1.0.23
            multidict == 4.7.6
            outcome == 1.0.1
            python-dateutil == 2.8.1
            requests == 2.23.0
            requests-toolbelt == 0.9.1
            six == 1.15.0
            sniffio == 1.1.0
            sortedcontainers == 2.2.2
            texttable == 1.6.2
            trio == 0.16.0
            trio-websocket == 0.8.0
            urllib3 == 1.25.9
            wsaccel == 0.6.2
            wsproto == 0.14.1
            yarl == 1.4.2
        ''',
        entry_points={
            'console_scripts': [
                'lager=lager.cli:cli',
            ],
        }
    )
