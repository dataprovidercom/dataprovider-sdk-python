from requests.exceptions import HTTPError

from dataprovider.sdk.client.api_client import ApiClient


def main():
    client = ApiClient('username', 'password')

    my_dataset_id = 1
    try:
        response = client.post(
            path=f'/datasets/{my_dataset_id}/statistics',
            body={'fields': ['hostname']}
        )
    except HTTPError as e:
        if e.response.status_code == 404:
            print('Dataset not found.')
        elif e.response.status_code == 429:
            print('Rate limit reached. Try again later.')
        else:
            print(f'An error occurred ({e.response.status_code}): {e.response.text}')
        return

    print(response.text)

if __name__ == '__main__':
    main()
