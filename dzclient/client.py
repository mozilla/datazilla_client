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

    """
    def __init__(self, results=None):
        self.results = results or {}

    def add_testsuite(self, suite_name, results=None):
        """Add a testsuite of {"testname":[values],...} to the results."""
        self.results[suite_name] = results or {}

    def add_test_results(self, suite_name, test_name, values):
        """Add a list of result values to the given testsuite/testname pair."""
        suite = self.results.setdefault(suite_name, {})
        suite.setdefault(test_name, []).extend(values)

    def join_results(self, results):
        """Add a dictionary of {"suite":{"name":[values], ...}} to results."""
        for suite_name, tests in results.items():
            suite = self.results.setdefault(suite_name, {})
            for test_name, values in tests.items():
                suite.setdefault(test_name, []).extend(values)

class DatazillaResultsCollection(object):
    """DatazillaResultsCollection manages test information and serialization to JSON"""

    def __init__(self, machine_name="", os="", os_version="", platform="",
                 build_name="", version="", revision="", branch="", id="",
                 test_date=None):
        """
        - id : the build ID for which the dzresults are for; a unique identifier to which these results belong
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
        self.results.join_results(res.results)

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
                'revision': self.revision[:16],
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
            datasets.append(dataset)

        return datasets


class DatazillaRequest(DatazillaResultsCollection):
    """
    Datazilla request object that manages test submission.

    Note that the revision id can be 16 characters, maximum.

    """

    @classmethod
    def create(cls, protocol, host, project, oauth_key,
                oauth_secret, collection):
        """create a DatazillaRequest instance from a results collection"""

        # get attributes from the collection
        attributes = inspect.getargspec(DatazillaResultsCollection.__init__).args[1:]
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

        if protocol in set(['http', 'https']):
            self.protocol = protocol
        else:
            #Default to https
            self.protocol = 'https'

        DatazillaResultsCollection.__init__(self, **kw)


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
            'oauth_version': "1.0",
            'oauth_nonce': oauth.generate_nonce(),
            'oauth_timestamp': int(time.time()),
            'user': user,
            'data': urllib.quote(json.dumps(dataset)),
        }

        #There is no requirement for the token in two-legged
        #OAuth but we still need the token object.
        token = oauth.Token(key="", secret="")
        consumer = oauth.Consumer(key=self.oauth_key, secret=self.oauth_secret)

        params['oauth_token'] = token.key
        params['oauth_consumer_key'] = consumer.key

        req = oauth.Request(method="POST", url=uri, parameters=params)

        #Set the signature
        signature_method = oauth.SignatureMethod_HMAC_SHA1()

        #Sign the request
        req.sign_request(signature_method, consumer, token)

        #Build the header
        header = {'Content-type': 'application/x-www-form-urlencoded'}

        conn = None
        if self.protocol == 'https':
            conn = httplib.HTTPSConnection(self.host)
        else:
            conn = httplib.HTTPConnection(self.host)

        conn.request("POST", path, req.to_postdata(), header)
        return conn.getresponse()
