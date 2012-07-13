from unittest import TestCase

from mock import patch

from ..datazilla import DatazillaRequest, DatazillaResult



class DatazillaRequestTest(TestCase):
    def test_init_with_date(self):
        """Can provide test date on instantiation."""
        req = DatazillaRequest('server', test_date=12345)

        self.assertEqual(req.test_date, 12345)


    def test_add_datazilla_result(self):
        """Can add a DatazillaResult to a DatazillaRequest."""
        req = DatazillaRequest('server')
        res = DatazillaResult({'suite': {'test': [1, 2, 3]}})

        req.add_datazilla_result(res)

        self.assertEqual(req.results.results, res.results)


    def test_add_second_datazilla_result(self):
        """Adding a second DatazillaResult joins their results."""
        req = DatazillaRequest('server')
        res1 = DatazillaResult({'suite1': {'test': [1]}})
        res2 = DatazillaResult({'suite2': {'test': [2]}})

        req.add_datazilla_result(res1)
        req.add_datazilla_result(res2)

        self.assertEqual(
            req.results.results,
            {'suite1': {'test': [1]}, 'suite2': {'test': [2]}},
            )


    @patch.object(DatazillaRequest, 'send')
    def test_submit(self, mock_send):
        """Submits blob of JSON data for each test suite."""
        req = DatazillaRequest(
            server='datazilla.mozilla.org/project/api/load_test',
            machine_name='qm-pxp01',
            os='linux',
            os_version='Ubuntu 11.10',
            platform='x86_64',
            build_name='Firefox',
            version='14.0a2',
            revision='785345035a3b',
            branch='Mozilla-Aurora',
            id='20120228122102',
            )

        req.add_datazilla_result(
            DatazillaResult(
                {'suite1': {'test1': [1]}, 'suite2': {'test2': [2]}}
                )
            )

        req.submit()

        self.assertEqual(mock_send.call_count, 2)
        data1 = mock_send.call_args_list[0][0][0]
        data2 = mock_send.call_args_list[1][0][0]

        results = sorted([data1.pop('results'), data2.pop('results')])

        self.assertEqual(results, sorted([{'test1': [1]}, {'test2': [2]}]))

        suites = sorted(
            [data1['testrun'].pop('suite'), data2['testrun'].pop('suite')])

        self.assertEqual(suites, sorted(['suite1', 'suite2']))

        # aside from results and suite, datasets are the same
        self.assertEqual(data1, data2)

        self.assertEqual(
            data1['test_build'],
            {
                'branch': 'Mozilla-Aurora',
                'id': '20120228122102',
                'name': 'Firefox',
                'revision': '785345035a3b',
                'version': '14.0a2',
                },
            )

        self.assertEqual(
            data1['test_machine'],
            {
                'name': 'qm-pxp01',
                'os': 'linux',
                'osversion': 'Ubuntu 11.10',
                'platform': 'x86_64',
                },
            )

        self.assertEqual(data1['testrun']['date'], req.test_date)


    @patch("datazilla.datazilla.urllib2.urlopen")
    def test_send(self, mock_urlopen):
        """Can send data to the server."""
        server = "datazilla.mozilla.org/project/api/load_test"
        req = DatazillaRequest(server)

        req.send({"some": "data"})

        self.assertEqual(mock_urlopen.call_count, 1)
        request = mock_urlopen.call_args[0][0]

        self.assertEqual(request.get_full_url(), server)

        self.assertEqual(
            request.get_data(), 'data=%7B%22some%22%3A+%22data%22%7D')

        self.assertEqual(
            request.headers['Content-type'],
            'application/x-www-form-urlencoded',
            )
