
import os
import setuptools

import lager

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
        version=lager.__version__,
        description=description,
        long_description=readme(),
        classifiers=classifiers,
        url='https://github.com/lagerdata/lager-cli',
        author=author,
        author_email=email,
        maintainer=author,
        maintainer_email=email,
        license='MIT',
        python_requires=">=3.5",
        packages=setuptools.find_packages(),
        install_requires=[
            'click',
            'requests',
        ],
        scripts=[
            'bin/lager',
        ],
    )
