import requests

from typing import Any
from urllib.parse import urlencode

from requests.models import Response


class ApiClient:
    """
    Client for interacting with the Dataprovider.com API.

    This client handles all communication with the Dataprovider.com platform, including
    authentication, request preparation, and response handling. It abstracts away the
    low-level HTTP details and provides a simple interface for executing authorized API calls.

    Use this client to send authenticated requests.

    Example usage:
        client = ApiClient('username', 'password')
        response = client.post(
            path=f'/datasets/{my_dataset_id}/statistics',
            body={'fields': ['hostname']}
        )

    Args:
        username (str): The API username.
        password (str): The API password.

    Returns:
        Response: The response from the API.
    """
    _HOST = 'https://api.dataprovider.com/v2'
    _AUTH_PATH = '/auth/oauth2/token'

    _username: str
    _password: str
    _access_token: str | None = None
    _refresh_token: str | None = None

    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password

    def get(self, path: str, params: dict[str, str] | None = None, body: dict[str, Any] | None = None) -> Response:
        """
        Send a GET request to the Dataprovider.com API.

        Args:
            path (str): The API endpoint path (relative, not full URL).
            params (dict[str, str] | None): Optional query parameters.
            body (dict[str, Any] | None): Optional request body (rarely used for GET).

        Returns:
            Response: The HTTP response from the API.
        """
        return self._do_request(path=path, method='GET', params=params, body=body)

    def post(self, path: str, params: dict[str, str] | None = None, body: dict[str, Any] | None = None) -> Response:
        """
        Send a POST request to the Dataprovider.com API.

        Args:
            path (str): The API endpoint path (relative, not full URL).
            params (dict[str, str] | None): Optional query parameters.
            body (dict[str, Any] | None): Optional request body.

        Returns:
            Response: The HTTP response from the API.
        """
        return self._do_request(path=path, method='POST', params=params, body=body)

    def put(self, path: str, params: dict[str, str] | None = None, body: dict[str, Any] | None = None) -> Response:
        """
        Send a PUT request to the Dataprovider.com API.

        Args:
            path (str): The API endpoint path (relative, not full URL).
            params (dict[str, str] | None): Optional query parameters.
            body (dict[str, Any] | None): Optional request body.

        Returns:
            Response: The HTTP response from the API.
        """
        return self._do_request(path=path, method='PUT', params=params, body=body)

    def _do_request(self, path: str, method: str, params: dict[str, str] | None, body: dict[str, Any] | None) -> Response:
        if not path:
            raise ValueError('Path cannot be empty.')
        if path.startswith('http'):
            raise ValueError('Path cannot contain a full url, please remove the host.')

        url = f'{self._HOST}/{path.lstrip('/')}'
        if params:
            url += '?' + urlencode(query=params)

        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Dataprovider.com - SDK (Python)'
        }

        if self._access_token is None and path != self._AUTH_PATH:
            self._authenticate()
            headers['Authorization'] = f'Bearer {self._access_token}'

        response = requests.request(
            method=method,
            url=url,
            json=body,
            headers=headers,
            timeout=60,
        )

        if response.status_code == 401 and self._access_token is not None:
            self._access_token = None
            return self._do_request(path, method, params, body)

        response.raise_for_status()

        return response

    def _authenticate(self):
        try:
            if self._refresh_token is None:
                response = self._get_access_token_by_credentials()
            else:
                response = self._get_access_token_by_refresh_token()
        except requests.RequestException as e:
            if self._refresh_token is not None:
                # Expired refresh token, try again with credentials
                self._refresh_token = None
                return self._authenticate()
            raise e

        body = response.json()
        self._access_token = body['access_token']
        self._refresh_token = body['refresh_token']

        return response

    def _get_access_token_by_credentials(self) -> Response:
        return self.post(
            path=self._AUTH_PATH,
            body={
                'grant_type': 'password',
                'username': self._username,
                'password': self._password
            }
        )

    def _get_access_token_by_refresh_token(self) -> Response:
        return self.post(
            path=self._AUTH_PATH,
            body={
                'grant_type': 'refresh_token',
                'refresh_token': self._refresh_token
            }
        )
