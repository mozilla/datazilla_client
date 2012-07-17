# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from copy import deepcopy
import urllib
import urllib2
import json
import time

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


class DatazillaRequest(object):
    """
    Datazilla request object that manages test information and submission.

    Note that the revision id can be 16 characters, maximum.

    """
    def __init__(self,
                 server, machine_name="", os="", os_version="", platform="",
                 build_name="", version="", revision="", branch="", id="",
                 test_date=None):
        self.server = server
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

    def submit(self):
        """Submit test data to datazilla server."""
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
                'suite': "",
            },
            'results': {},
        }

        datasets = []
        for suite, data in self.results.results.items():
            perf_json['testrun']['suite'] = suite
            perf_json['results'] = data;
            datasets.append(deepcopy(perf_json))
            perf_json['results'] = {}

        for dataset in datasets:
            self.send(dataset)


    def send(self, dataset):
        """Send given dataset to server."""
        data = {"data": json.dumps(dataset)}
        req = urllib2.Request(
            self.server,
            urllib.urlencode(data),
            {'Content-Type': 'application/x-www-form-urlencoded'},
            )
        urllib2.urlopen(req)
