# Flask-Weaviate

[![PyPI Version](https://img.shields.io/pypi/v/flask-weaviate.svg)](https://pypi.org/project/flask-weaviate/)
[![Code Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)](.coverage)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)


Flask-Weaviate is a Flask extension for integrating Weaviate into Flask applications. It provides a convenient way to manage a Weaviate client connection, supporting configuration through Flask app settings and environment variables.

## Installation

Install Flask-Weaviate using pip:

```bash
pip install flask-weaviate
```

## Usage

Initialize the extension in your Flask app:

```python
from flask import Flask
from flask_weaviate import FlaskWeaviate

app = Flask(__name__)
weaviate = FlaskWeaviate(app)
```

Access the Weaviate client within your Flask app:

```python
weaviate_client = weaviate.client
# Now you can use weaviate_client to interact with Weaviate
```

Automatically disconnects the Weaviate client during app context teardown.

### Flask app factory:

```python
from flask import Flask, jsonify
from flask_weaviate import FlaskWeaviate

weaviate = FlaskWeaviate()

def create_app():
    app = Flask(__name__)
    weaviate.init_app(app)

    @app.route('/')
    def index():
        # Access the Weaviate client
        client = weaviate.client

        # Now you can use client to interact with Weaviate
        # ...

        return jsonify({'message': 'Hello, Weaviate!'})

    # Your other app configurations and extensions

    return app

if __name__ == '__main__':
    create_app().run()
```

## Configuration

The following configuration parameters can be set in the Flask app's configuration or as environment variables:

- `WEAVIATE_HTTP_HOST`: Weaviate server HTTP host.
- `WEAVIATE_HTTP_PORT`: Weaviate server HTTP port.
- `WEAVIATE_HTTP_SECURE`: Use HTTP secure connection to the Weaviate server (True/False).
- `WEAVIATE_GRPC_HOST`: Weaviate server gRPC host.
- `WEAVIATE_GRPC_PORT`: Weaviate server gRPC port.
- `WEAVIATE_GRPC_SECURE`: Use gRPC secure connection to the Weaviate server (True/False).
- `WEAVIATE_API_KEY`: API key for authentication with Weaviate.
- `WEAVIATE_USERNAME`: Username for authentication (used with password).
- `WEAVIATE_PASSWORD`: Password for authentication (used with username).
- `WEAVIATE_ACCESS_TOKEN`: Access token for authentication with Weaviate.
- `WEAVIATE_CONNECTION_PARAMS`: Weaviate client connection parameters.
- `WEAVIATE_EMBEDDED_OPTIONS`: Options for embedded Weaviate.
- `WEAVIATE_AUTH_CLIENT_SECRET`: Auth client secret for Weaviate.
- `WEAVIATE_ADDITIONAL_HEADERS`: Additional headers for Weaviate requests.
- `WEAVIATE_ADDITIONAL_CONFIG`: Additional configuration for Weaviate.
- `WEAVIATE_SKIP_INIT_CHECKS`: Skip Weaviate client initialization checks.

#### Connection

When any of `http_host` `http_port` `http_secure` `grpc_host` `grpc_port` `grpc_secure` is set, 
the connection is created with these values as connection params

Else if `connection_params` are given, they are used to connect

Else Weaviate is stared in Embedded mode standard (either with delivered `embedded_options` or defaults)

#### Authentication

Authentication is determined from sequence: `api_key`, `username + password`, `access_token`.
If the first in sequence is detected the others are skipped.

### Example

```python
from flask import Flask, jsonify
from flask_weaviate import FlaskWeaviate

app = Flask(__name__)
weaviate = FlaskWeaviate(
    app,
    http_host="weaviate-server",
    http_port=80,
    http_secure=False,
    api_key="your-api-key",
    skip_init_checks=True
)

@app.route('/')
def index():
    # Access the Weaviate client
    weaviate_client = weaviate.client

    # Now you can use weaviate_client to interact with Weaviate
    # ...

    return jsonify({'message': 'Hello, Weaviate!'})

if __name__ == '__main__':
    app.run()
```

## Teardown Function

Flask-Weaviate includes a teardown function to automatically disconnect the Weaviate client during app context teardown. This ensures proper cleanup of resources.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
