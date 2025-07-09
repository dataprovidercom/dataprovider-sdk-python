from requests.exceptions import HTTPError

from dataprovider.sdk.client.api_client import ApiClient


def main():
    client = ApiClient('username', 'password')

    try:
        response = client.post(
            path='search-engine/hostnames/www.dataprovider.com',
            body={'fields': ['hostname', 'response']}
        )
    except HTTPError as e:
        if e.response.status_code == 404:
            print('Hostname not found.')
        elif e.response.status_code == 429:
            print('Rate limit reached. Try again later.')
        else:
            print(f'An error occurred ({e.response.status_code}): {e.response.text}')
        return

    print(response.text)

if __name__ == '__main__':
    main()
