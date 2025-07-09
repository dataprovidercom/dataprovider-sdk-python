# Dataprovider.com Python SDK

A lightweight SDK for interacting with the [Dataprovider.com](https://api.dataprovider.com/v2/docs) API in Python.\
This client provides a convenient way to authenticate, build requests, and handle responses for GET, POST, and PUT operations.

## 🚀 Installation

Use [PIP](https://pypi.org/project/pip/) to install the SDK:

```bash
pip install dataprovider-sdk
```

## ✅ Requirements

- Python >= 3.13
- PIP for dependency management

## 🔧 Usage

```python
from requests.exceptions import HTTPError
from dataprovider.sdk.client.api_client import ApiClient

def main():
    client = ApiClient('username', 'password')

    try:
        response = client.get(path='/datasets/list')
    except HTTPError as e:
        print(f'An error occurred ({e.response.status_code}): {e.response.text}')
        return

    # Access the response data as text
    print(response.text)

    # Access the response data as dict
    print(response.json())

if __name__ == '__main__':
    main()
```

See [examples](examples) for more.