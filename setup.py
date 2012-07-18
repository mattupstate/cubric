"""
Cubric
--------------

Cubric allows you to easily create and configure servers for arbitrary WSGI
applications on Amazon EC2 or Rackspace Cloud Servers


Links
`````

* `development version
  <https://github.com/mattupstate/cubric/raw/develop#egg=Cubric-dev>`_

"""
import os
from setuptools import setup


def fullsplit(path, result=None):
    """Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

packages = []
root_dir = os.path.dirname(__file__)

if root_dir != '':
    os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk('cubric'):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'):
            del dirnames[i]

    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))

setup(
    name='Cubric',
    version='0.1.0',
    url='https://github.com/mattupstate/cubric',
    license='MIT',
    author='Matthew Wright',
    author_email='matt@nobien.net',
    description='Simple server creation and configuration on EC2 and Rackspace',
    long_description=__doc__,
    packages=packages,
    zip_safe=False,
    platforms='any',
    install_requires=['cuisine'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
