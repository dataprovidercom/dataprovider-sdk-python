import unittest
from unittest.mock import patch, Mock

from requests.exceptions import RequestException
from requests.models import Response
from dataprovider.sdk.client.api_client import ApiClient


class TestApiClient(unittest.TestCase):
    def setUp(self):
        self.client = ApiClient('test', 'test')

    def make_response(self, status_code=200, json_data=None):
        import json as py_json

        response = Mock(spec=Response)
        response.status_code = status_code
        response.json.return_value = json_data
        response.text = py_json.dumps(json_data)

        def raise_for_status():
            if status_code != 200:
                raise RequestException(f'{status_code} Client Error: {response.text}')

        response.raise_for_status.side_effect = raise_for_status

        return response

    @patch('requests.request')
    def test_requests_return_valid_response(self, mock_request):
        mock_request.side_effect = [
            self.make_response(json_data={'access_token': 'abc', 'refresh_token': 'xyz'}),
            self.make_response(json_data={'type': 'get'}),
            self.make_response(json_data={'type': 'post'}),
            self.make_response(json_data={'type': 'put'}),
        ]

        get_resp = self.client.get('test/get')
        self.assertEqual(get_resp.json()['type'], 'get')

        post_resp = self.client.post('test/post', params={'test': 'test'}, body={'id': 1})
        self.assertEqual(post_resp.json()['type'], 'post')

        put_resp = self.client.put('test/put', body={'id': 1})
        self.assertEqual(put_resp.json()['type'], 'put')

        calls = mock_request.call_args_list
        self.assertEqual(calls[1].kwargs['method'], 'GET')
        self.assertNotIn('?', calls[1].kwargs['url'])
        self.assertEqual(
            calls[1].kwargs['headers']['Authorization'], 'Bearer abc'
        )
        self.assertIsNone(calls[1].kwargs.get('json'))

        self.assertEqual(calls[2].kwargs['method'], 'POST')
        self.assertIn('?test=test', calls[2].kwargs['url'])
        self.assertEqual(calls[2].kwargs['json'], {'id': 1})

        self.assertEqual(calls[3].kwargs['method'], 'PUT')
        self.assertNotIn('?', calls[3].kwargs['url'])
        self.assertEqual(calls[3].kwargs['json'], {'id': 1})

    @patch('requests.request')
    def test_token_refresh(self, mock_request):
        mock_request.side_effect = [
            self.make_response(json_data={'access_token': 'abc', 'refresh_token': 'def'}),
            self.make_response(status_code=401, json_data='{"error":{"message":"Forbidden: Invalid credentials or token.","request_id":"1234-5678"}}'),
            self.make_response(json_data={'access_token': 'ghi', 'refresh_token': 'jkl'}),
            self.make_response(json_data={'status': 'ok'})
        ]

        resp = self.client.post('test')
        self.assertEqual(resp.json()['status'], 'ok')

        calls = mock_request.call_args_list
        urls = [c.kwargs['url'] for c in calls]
        bodies = [c.kwargs.get('json') for c in calls]
        headers = [c.kwargs['headers'] for c in calls]

        self.assertEqual(urls, [
            'https://api.dataprovider.com/v2/auth/oauth2/token',
            'https://api.dataprovider.com/v2/test',
            'https://api.dataprovider.com/v2/auth/oauth2/token',
            'https://api.dataprovider.com/v2/test',
        ])
        self.assertEqual(bodies, [
            {'grant_type': 'password', 'username': 'test', 'password': 'test'},
            None,
            {'grant_type': 'refresh_token', 'refresh_token': 'def'},
            None
        ])
        self.assertEqual(headers, [
            {'Content-Type': 'application/json', 'User-Agent': 'Dataprovider.com - SDK (Python)'},
            {'Authorization': 'Bearer abc', 'Content-Type': 'application/json', 'User-Agent': 'Dataprovider.com - SDK (Python)'},
            {'Content-Type': 'application/json', 'User-Agent': 'Dataprovider.com - SDK (Python)'},
            {'Authorization': 'Bearer ghi', 'Content-Type': 'application/json', 'User-Agent': 'Dataprovider.com - SDK (Python)'}
        ])

    @patch('requests.request')
    def test_auth_refresh_failure_falls_back_to_credentials(self, mock_request):
        mock_request.side_effect = [
            self.make_response(json_data={'access_token': 'abc', 'refresh_token': 'def'}),
            self.make_response(status_code=401, json_data='{"error":{"message":"Forbidden: Invalid credentials or token.","request_id":"1234-5678"}}'),
            self.make_response(status_code=401, json_data='{"error":{"message":"Forbidden: Invalid credentials or token.","request_id":"1234-5678"}}'),
            self.make_response(json_data={'access_token': 'ghi', 'refresh_token': 'jkl'}),
            self.make_response(json_data={'status': 'ok'})
        ]

        resp = self.client.post('test')
        self.assertEqual(resp.json()['status'], 'ok')

        calls = mock_request.call_args_list
        urls = [c.kwargs['url'] for c in calls]
        bodies = [c.kwargs.get('json') for c in calls]
        headers = [c.kwargs['headers'] for c in calls]

        self.assertEqual(urls, [
            'https://api.dataprovider.com/v2/auth/oauth2/token',
            'https://api.dataprovider.com/v2/test',
            'https://api.dataprovider.com/v2/auth/oauth2/token',
            'https://api.dataprovider.com/v2/auth/oauth2/token',
            'https://api.dataprovider.com/v2/test',
        ])
        self.assertEqual(bodies, [
            {'grant_type': 'password', 'username': 'test', 'password': 'test'},
            None,
            {'grant_type': 'refresh_token', 'refresh_token': 'def'},
            {'grant_type': 'password', 'username': 'test', 'password': 'test'},
            None
        ])
        self.assertEqual(headers, [
            {'Content-Type': 'application/json', 'User-Agent': 'Dataprovider.com - SDK (Python)'},
            {'Authorization': 'Bearer abc', 'Content-Type': 'application/json', 'User-Agent': 'Dataprovider.com - SDK (Python)'},
            {'Content-Type': 'application/json', 'User-Agent': 'Dataprovider.com - SDK (Python)'},
            {'Content-Type': 'application/json', 'User-Agent': 'Dataprovider.com - SDK (Python)'},
            {'Authorization': 'Bearer ghi', 'Content-Type': 'application/json', 'User-Agent': 'Dataprovider.com - SDK (Python)'}
        ])

    @patch('requests.request')
    def test_auth_refresh_failure_falls_back_to_credentials_fail(self, mock_request):
        mock_request.side_effect = [
            self.make_response(
                status_code=200,
                json_data={'access_token': 'abc', 'refresh_token': 'def'}
            ),
            self.make_response(
                status_code=401,
                json_data={'error':{'message':'Forbidden: Invalid credentials or token.','request_id':'1234-5678'}},
            ),
            self.make_response(
                status_code=401,
                json_data={'error':{'message':'Forbidden: Invalid credentials or token.','request_id':'1234-5678'}},
            ),
            self.make_response(
                status_code=401,
                json_data={'error':{'message':'Forbidden: Invalid credentials or token.','request_id':'1234-5678'}},
            )
        ]

        response = None
        exception = None

        try:
            response = self.client.post('test')
        except RequestException as e:
            exception = e

        self.assertIsNone(response)
        self.assertIsNotNone(exception)
        self.assertEqual(
            str(exception),
            '401 Client Error: {"error": {"message": "Forbidden: Invalid credentials or token.", "request_id": "1234-5678"}}'
        )

        calls = mock_request.call_args_list
        urls = [c.kwargs['url'] for c in calls]
        bodies = [c.kwargs.get('json') for c in calls]
        headers = [c.kwargs['headers'] for c in calls]

        expected_urls = [
            'https://api.dataprovider.com/v2/auth/oauth2/token',
            'https://api.dataprovider.com/v2/test',
            'https://api.dataprovider.com/v2/auth/oauth2/token',
            'https://api.dataprovider.com/v2/auth/oauth2/token',
        ]

        expected_bodies = [
            {'grant_type': 'password', 'username': 'test', 'password': 'test'},
            None,
            {'grant_type': 'refresh_token', 'refresh_token': 'def'},
            {'grant_type': 'password', 'username': 'test', 'password': 'test'},
        ]

        expected_headers = [
            {'Content-Type': 'application/json', 'User-Agent': 'Dataprovider.com - SDK (Python)'},
            {'Authorization': 'Bearer abc', 'Content-Type': 'application/json', 'User-Agent': 'Dataprovider.com - SDK (Python)'},
            {'Content-Type': 'application/json', 'User-Agent': 'Dataprovider.com - SDK (Python)'},
            {'Content-Type': 'application/json', 'User-Agent': 'Dataprovider.com - SDK (Python)'}
        ]

        self.assertEqual(urls, expected_urls)
        self.assertEqual(bodies, expected_bodies)

        for expected, actual in zip(expected_headers, headers):
            for k, v in expected.items():
                self.assertEqual(actual.get(k), v)

    def test_client_throws_on_empty_path(self):
        with self.assertRaises(ValueError) as ctx:
            self.client.post('')
        self.assertIn('Path cannot be empty.', str(ctx.exception))

    def test_client_throws_on_full_url(self):
        with self.assertRaises(ValueError) as ctx:
            self.client.get('https://api.dataprovider.com/v2/test')
        self.assertIn('Path cannot contain a full url, please remove the host.', str(ctx.exception))

    @patch('requests.request')
    def test_throw_for_client_error_status(self, mock_request):
        mock_request.side_effect = RequestException('400 Client Error: Bad Request')
        with self.assertRaises(RequestException) as ctx:
            self.client.get('test/error')
        self.assertIn('400 Client Error', str(ctx.exception))
