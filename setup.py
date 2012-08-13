# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from setuptools import setup

version = '1.0'

deps = ['oauth2']

try:
    import json
except ImportError:
    deps.append('simplejson')

setup(name='datazilla',
      version=version,
      description="Python library to interact with the datazilla server",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Malini Das',
      author_email='mdas@mozilla.com',
      url='https://github.com/mozilla/datazilla_client',
      license='MPL',
      packages=['dzclient'],
      zip_safe=False,
      install_requires=deps,
      test_suite='dzclient.tests',
      tests_require=["mock"],
      )
