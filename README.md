datazilla_client
================

Client libraries to interact with the datazilla database.

Usage
-----

    from datazilla import DatazillaRequest, DatazillaResult
    
    res = DatazillaResult()
    res.add_testsuite("suite_name", {"test_name": [1, 2, 3]})
    res.add_test_results("suite_name", "another_test", [2, 3, 4])
    
    req = DatazillaRequest(
        server="datazilla.mozilla.org/project/api/load_test",
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
