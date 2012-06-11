# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from copy import deepcopy
import urllib
import urllib2
import json
import time

"""
This is a helper class for managing testsuites and their test results
Currently, the results are a dictionary of {"testsuite":{"testname":[values], ...}} 
"""
class DatazillaResult(object):
    def __init__(self, results={}):
      self.results = results
    
    """
    Add a testsuite of {"testname":[values],...} to the results
    """
    def add_testsuite(self, suite_name, results={}):
        self.results[suite_name] = results
        
    """
    Adds a list of result values to the results in the given testsuite/testname pair 
    """
    def add_test_results(self, suite_name, test_name, values):
        if self.results.has_key(suite_name):
            if self.results[suite_name].has_key(test_name):
                self.results[suite_name][test_name].extend(values)
            else:
                self.results[suite_name][test_name] = values

    """
    Add a dictionary of {"testsuite":{"testname":[values], ...}} to the results
    """
    def join_results(self, results):
        for suite in results:
             if self.results.has_key(suite):
                for test in results[suite]:
                    self.results[suite][test].extend(results[suite][test])
             else:
                self.results[suite] = results[suite]

"""
Datazilla request object that manages test information and submission
"""
class DatazillaRequest(object):
    def __init__(self, server, machine_name="", os="", os_version="", platform="",
                 build_name="", version="", revision="", branch="", id="",
                 test_date=int(time.time())):
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
        self.test_date = test_date
        self.results = DatazillaResult()   
        
    """
    Join a DatazillaResult object to the results
    """
    def add_datazilla_result(self, res):
        self.results.join_results(res.results)

    """
    Submit test data to datazilla server
    """
    def submit(self):
        if self.server is None:
            raise "Data server is not set!"

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
                'revision': self.revision,
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
            data = {"data": json.dumps(dataset)}
            req = urllib2.Request(self.server, urllib.urlencode(data))

