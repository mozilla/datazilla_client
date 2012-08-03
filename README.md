datazilla_client
================

Client libraries to interact with the datazilla database.

Usage
-----

    from dzclient import DatazillaRequest, DatazillaResult

    res = DatazillaResult()
    res.add_testsuite("suite_name", {"test_name": [1, 2, 3]})
    res.add_test_results("suite_name", "another_test", [2, 3, 4])

    req = DatazillaRequest(
        protocol="https",
        host="datazilla.mozilla.org",
        project="project",
        oauth_key="oauth-key",
        oauth_secret="oauth-secret",
        machine_name="qm-pxp01",
        os="linux",
        os_version="Ubuntu 11.10",
        platform="x86_64",
        build_name="Firefox",
        version="14.0a2",
        revision="785345035a3b",
        branch="Mozilla-Aurora",
        id="20120228122102",
        )
    req.add_datazilla_result(res)
    req.submit()

The OAuth key and secret for your project should be supplied to you by the
Datazilla team.

If you don't want to use `DatazillaResult` to build up the data structure to
send, you can still use `DatazillaRequest` to send it:

    req = DatazillaRequest(
        protocol="https",
        host="datazilla.mozilla.org",
        project="project",
        oauth_key="oauth-key",
        oauth_secret="oauth-secret",
        )
    data_to_send = ...
    req.send(data_to_send)

You may also introspect the data to be sent by the `DatazillaRequest`:

    req.datasets()
    [{'test_machine': {'platform': 'x86_64', 'osversion': 'Ubuntu 11.10', 'os': 'linux', 'name': 'qm-pxp01'}, 'testrun': {'date': 1343062245, 'suite': 'suite_name'}, 'results': {'another_test': [2, 3, 4], 'test_name': [1, 2, 3]}, 'test_build': {'version': '14.0a2', 'revision': '785345035a3b', 'id': '20120228122102', 'branch': 'Mozilla-Aurora', 'name': 'Firefox'}}]


Development
-----------

To run the `datazilla_client` test suite, run `python setup.py test`.

If you have `python2.5`, `python2.6`, and `python2.7` available on your system
under those names, you can also `pip install tox` and then run `tox` to test
`datazilla_client` under all of those Python versions.
