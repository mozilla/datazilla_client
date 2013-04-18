# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import inspect
import httplib
import oauth2 as oauth
import time
import urllib
from copy import deepcopy
from urlparse import urlparse

try:
    import json
except ImportError:
    import simplejson as json

class DatazillaResult(object):
    """
    A helper class for managing testsuites and their test results.

    Currently, the results are a dictionary of
    {"testsuite":{"testname":[values], ...}}


    Each suite may also have an options dictionary
    """
    def __init__(self, results=None, results_aux=None, results_xperf=None, options=None):
        self.results = results or {}
        self.results_aux = results_aux or {}
        self.results_xperf = results_xperf or {}
        self.options = options or {}

    def add_testsuite(self, suite_name, results=None, results_aux=None, results_xperf=None, options=None):
        """Add a testsuite of {"testname":[values],...} to the results."""
        self.results[suite_name] = results or {}
        self.results_aux[suite_name] = results_aux or {}
        self.results_xperf[suite_name] = results_xperf or {}
        self.options[suite_name] = options or {}

    def add_test_results(self, suite_name, test_name, values):
        """Add a list of result values to the given testsuite/testname pair."""
        suite = self.results.setdefault(suite_name, {})
        suite.setdefault(test_name, []).extend(values)

    def add_auxiliary_results(self, suite_name, results_name, values):
        """Add auxiliary results for a test suite"""
        suite = self.results_aux.setdefault(suite_name, {})
        suite.setdefault(results_name, []).extend(values)

    def add_xperf_results(self, suite_name, results_name, values):
        """Add auxiliary results for a test suite"""
        suite = self.results_xperf.setdefault(suite_name, {})
        suite.setdefault(results_name, []).extend(values)

    def join_results(self, results):
        """merge an existing DatazillaResult instance with this one"""

        for suite_name, tests in results.results.items():
            suite = self.results.setdefault(suite_name, {})
            for test_name, values in tests.items():
                suite.setdefault(test_name, []).extend(values)
        for suite_name, results_aux in results.results_aux.items():
            suite = self.results_aux.setdefault(suite_name, {})
            for results_name, values in results_aux.items():
                suite.setdefault(results_name, []).extend(values)
        for suite_name, results_xperf in results.results_xperf.items():
            suite = self.results_xperf.setdefault(suite_name, {})
            for results_name, values in results_xperf.items():
                suite.setdefault(results_name, []).extend(values)
        for suite_name, options in results.options.items():
            self.options.setdefault(suite_name, {}).update(options)


class DatazillaResultsCollection(object):
    """DatazillaResultsCollection manages test information and serialization to JSON"""

    def __init__(self, machine_name="", os="", os_version="", platform="",
                 build_name="", version="", revision="", branch="", id="",
                 test_date=None):
        """
        - machine_name: host name of the test machine
        - os: name of the os of the test machine ('linux', 'win', 'mac')
        - os_version: long string of os version
        - platform: processor name, e.g. x86_64
        - build_name: name of the product under test, e.g. Firefox
        - version: version of the product under test
        - revision: source stamp of the product, if available
        - branch: branch of the product under test
        - id: the build ID for which the dzresults are for; a unique identifier to which these results belong
        - test_date: time stamp (seconds since epoch) of the test run, or now if not specified
        """

        self.machine_name = machine_name
        self.os = os
        self.os_version = os_version
        self.platform = platform
        self.build_name = build_name
        self.version = version
        self.revision = revision
        self.branch = branch
        self.id = id
        if test_date is None:
            test_date = int(time.time())
        self.test_date = test_date
        self.results = DatazillaResult()

    def add_datazilla_result(self, res):
        """Join a DatazillaResult object to the results."""
        self.results.join_results(res)

    def datasets(self):
        """Return the datasets in JSON serializable form"""

        perf_json = {
            'test_machine' : {
                'name': self.machine_name,
                'os' : self.os,
                'osversion': self.os_version,
                'platform': self.platform
            },
            'test_build' : {
                'name': self.build_name,
                'version': self.version,
                'revision': self.revision[:50],
                'branch': self.branch,
                'id': self.id
            },
            'testrun' : {
                'date': self.test_date,
            }
        }

        datasets = []
        for suite, data in self.results.results.items():
            dataset = deepcopy(perf_json)
            dataset['testrun']['suite'] = suite
            dataset['results'] = deepcopy(data)
            options = self.results.options.get(suite)
            if options:
                dataset['testrun']['options'] = deepcopy(options)
            results_aux = self.results.results_aux.get(suite)
            if results_aux:
                dataset['results_aux'] = deepcopy(results_aux)
            results_xperf = self.results.results_xperf.get(suite)
            if results_xperf:
                dataset['results_xperf'] = deepcopy(results_xperf)
            datasets.append(dataset)

        return datasets


class DatazillaRequest(DatazillaResultsCollection):
    """
    Datazilla request object that manages test submission.

    Note that the revision id can be 16 characters, maximum.

    """

    protocols = set(['http', 'https']) # supported protocols

    @classmethod
    def create(cls, protocol, host, project, oauth_key,
                oauth_secret, collection):
        """create a DatazillaRequest instance from a results collection"""

        # get attributes from the collection
        attributes, _, _, _ = inspect.getargspec(DatazillaResultsCollection.__init__)
        attributes = attributes[1:] # remove `self`
        kw = dict([(i, getattr(collection, i))
                   for i in attributes])

        # create the instance
        instance = cls(protocol, host, project, oauth_key, oauth_secret, **kw)

        # add the results
        instance.add_datazilla_result(collection.results)

        return instance

    def __init__(self, protocol, host, project, oauth_key, oauth_secret, **kw):
        """
        - host : datazilla host to post to
        - project : name of the project in datazilla: http://host/project
        - oauth_key, oauth_secret : oauth credentials
        - **kw : arguments to DatazillaResultsCollection.__init__
        """

        self.host = host
        self.project = project
        self.oauth_key = oauth_key
        self.oauth_secret = oauth_secret

        if protocol not in self.protocols:
            raise AssertionError("Protocol '%s' not supported; please use one of %s" %
                                 (protocol, ', '.join(self.protocols)))
        self.protocol = protocol

        DatazillaResultsCollection.__init__(self, **kw)

        # ensure the required parameters are given
        assert self.branch, "%s: branch required for posting" % (self.__class__.__name__)

    def submit(self):
        """Submit test data to datazilla server, return list of responses."""

        responses = []
        for dataset in self.datasets():
            responses.append(self.send(dataset))

        return responses

    def send(self, dataset):
        """Send given dataset to server; returns httplib Response."""
        path = "/%s/api/load_test" % (self.project)
        uri = "%s://%s%s" % (self.protocol, self.host, path)
        user = self.project

        params = {
            'data': urllib.quote(json.dumps(dataset)),
        }

        use_oauth = bool(self.oauth_key and self.oauth_secret)
        if use_oauth:

            params.update({'user': user,
                           'oauth_version': "1.0",
                           'oauth_nonce': oauth.generate_nonce(),
                           'oauth_timestamp': int(time.time())})


            # There is no requirement for the token in two-legged
            # OAuth but we still need the token object.
            token = oauth.Token(key="", secret="")
            consumer = oauth.Consumer(key=self.oauth_key, secret=self.oauth_secret)

            params['oauth_token'] = token.key
            params['oauth_consumer_key'] = consumer.key

            try:
                req = oauth.Request(method="POST", url=uri, parameters=params)
            except AssertionError, e:
                print 'uri: %s' % uri
                print 'params: %s' % params
                raise

            # Set the signature
            signature_method = oauth.SignatureMethod_HMAC_SHA1()

            # Sign the request
            req.sign_request(signature_method, consumer, token)
            body = req.to_postdata()
        else:
            body = urllib.urlencode(params)

        # Build the header
        header = {'Content-type': 'application/x-www-form-urlencoded'}

        # Make the POST request
        conn = None
        if self.protocol == 'http':
            conn = httplib.HTTPConnection(self.host)
        else:
            conn = httplib.HTTPSConnection(self.host)

        conn.request("POST", path, body, header)
        return conn.getresponse()
