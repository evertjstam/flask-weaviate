# Check for required dependencies
from functools import wraps

try:
    import flask  # noqa: F401
except ImportError:
    raise ImportError(
        "Flask-Weaviate requires the 'Flask' library. "
        "Install it using 'pip install Flask'."
    )

try:
    import weaviate  # noqa: F401
except ImportError:
    raise ImportError(
        "Flask-Weaviate requires the 'weaviate_client' library. "
        "Install it using 'pip install weaviate'."
    )

from typing import Dict, Optional, Union

from flask import Flask, current_app, has_app_context
from weaviate import WeaviateClient
from weaviate.auth import (
    AuthApiKey,
    AuthBearerToken,
    AuthClientPassword,
    _APIKey,
    _BearerToken,
    _ClientCredentials,
    _ClientPassword, Auth,
)
from weaviate.config import AdditionalConfig
from weaviate.connect import ConnectionParams
from weaviate.embedded import EmbeddedOptions
from weaviate.exceptions import WeaviateStartUpError


class FlaskWeaviate(object):
    """
    A Flask extension for managing a Weaviate client connection.

    This extension provides a convenient way to integrate a
    Weaviate client into a Flask application.
    It supports configuration through Flask app settings and
    automatically connects and disconnects
    the Weaviate client during app context setup and teardown.

    :param app: The Flask app to initialize the extension with.
    :type app: Flask | None
    :param http_host: The HTTP host of the Weaviate server.
    :type http_host: str | None
    :param http_port: The HTTP port of the Weaviate server.
    :type http_port: int | None
    :param http_secure: Use HTTP secure connection (https)
    :type http_secure: bool
    :param grpc_host: The gRPC host of the Weaviate server.
    :type grpc_host: str | None
    :param grpc_port: The gRPC port of the Weaviate server.
    :type grpc_port: int | None
    :param grpc_secure: Use gRPC secure connection to the Weaviate server.
    :type grpc_secure: bool
    :param api_key: API key for authentication with Weaviate.
    :type api_key: str | None
    :param username: Username for authentication (used with password).
    :type username: str | None
    :param password: Password for authentication (used with username).
    :type password: str | None
    :param access_token: Access token for authentication with Weaviate.
    :type access_token: str | None
    :param connection_params: Weaviate client connection parameters.
    :type connection_params: ConnectionParams | None
    :param embedded_options: Options for embedded Weaviate.
    :type embedded_options: EmbeddedOptions | None
    :param auth_client_secret: Auth client secret for Weaviate.
    :type auth_client_secret: _BearerToken | _ClientPassword |
    _ClientCredentials | _APIKey | None
    :param additional_headers: Additional headers for Weaviate requests.
    :type additional_headers: Dict | None
    :param additional_config: Additional configuration for Weaviate.
    :type additional_config: AdditionalConfig | None
    :param skip_init_checks: Skip Weaviate client initialization checks.
    :type skip_init_checks: bool

    Usage:
    ------
    1. Initialize the extension in your Flask app:

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

    Example with Flask app factory:
    --------
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

    Configuration:
    --------------
    The following configuration parameters can be set
    in the Flask app's configuration:

    - `WEAVIATE_HTTP_HOST`: Weaviate server HTTP host.
    - `WEAVIATE_HTTP_PORT`: Weaviate server HTTP port.
    - `WEAVIATE_HTTP_SECURE`: Use HTTP secure connection
    to the Weaviate server (True/False).
    - `WEAVIATE_GRPC_HOST`: Weaviate server gRPC host.
    - `WEAVIATE_GRPC_PORT`: Weaviate server gRPC port.
    - `WEAVIATE_GRPC_SECURE`: Use gRPC secure connection
    to the Weaviate server (True/False).
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

    """

    def __init__(
        self,
        app: Flask = None,
        http_host: str = None,
        http_port: int = None,
        http_secure: bool = None,
        grpc_host: str = None,
        grpc_port: int = None,
        grpc_secure: bool = None,
        api_key: str = None,
        username: str = None,
        password: str = None,
        access_token: str = None,
        connection_params: Optional[ConnectionParams] = None,
        embedded_options: Optional[EmbeddedOptions] = EmbeddedOptions(),
        auth_client_secret: Optional[
            Union[_BearerToken, _ClientPassword, _ClientCredentials, _APIKey]
        ] = None,
        additional_headers: Optional[Dict] = None,
        additional_config: Optional[AdditionalConfig] = None,
        skip_init_checks: bool = False,
    ):
        self._client = None
        # Connection check. first check setup with params,
        # then connection params else embedded is set as standard
        if any(
            x is not None
            for x in [
                http_host,
                http_port,
                http_secure,
                grpc_host,
                grpc_port,
                grpc_secure,
            ]
        ):
            self.connection_params = ConnectionParams.from_params(
                http_host=http_host or "localhost",
                http_port=http_port or 80,
                http_secure=http_secure or False,
                grpc_host=grpc_host or "localhost",
                grpc_port=grpc_port or 50051,
                grpc_secure=grpc_secure or False,
            )
            self.embedded_options = None
        elif connection_params is not None:
            self.connection_params = connection_params
            self.embedded_options = None
        else:
            self.embedded_options = embedded_options
            self.connection_params = None

        # check auth setup
        if api_key is not None:
            self.auth_client_secret = Auth.api_key(api_key)
        elif username is not None and password is not None:
            self.auth_client_secret = Auth.client_password(
                username=username, password=password
            )
        elif access_token is not None:
            self.auth_client_secret = Auth.bearer_token(access_token=access_token)
        else:
            self.auth_client_secret = auth_client_secret

        # Additional params
        self.additional_headers = additional_headers
        self.additional_config = additional_config
        self.skip_init_checks = skip_init_checks
        if self.connection_params is None and self.embedded_options is None:
            raise ValueError(
                "Both connection_params and embedded_options cannot be None."
            )
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> Flask:
        """
        Initialize the FlaskWeaviate extension with a Flask app.

        :param app: The Flask app to initialize the extension with.
        :type app: Flask
        """
        if any(
            x is not None
            for x in [
                app.config.get("WEAVIATE_HTTP_HOST"),
                app.config.get("WEAVIATE_HTTP_PORT"),
            ]
        ):
            self.connection_params = ConnectionParams.from_params(
                http_host=app.config.get("WEAVIATE_HTTP_HOST", "localhost"),
                http_port=app.config.get("WEAVIATE_HTTP_PORT", 80),
                http_secure=app.config.get("WEAVIATE_HTTP_SECURE", False),
                grpc_host=app.config.get("WEAVIATE_GRPC_HOST", "localhost"),
                grpc_port=app.config.get("WEAVIATE_GRPC_PORT", 50051),
                grpc_secure=app.config.get("WEAVIATE_GRPC_SECURE", False),
            )
            self.embedded_options = None
        elif app.config.get("WEAVIATE_CONNECTION_PARAMS") is not None:
            self.connection_params = app.config.get("WEAVIATE_CONNECTION_PARAMS")
            self.embedded_options = None
        elif app.config.get("WEAVIATE_EMBEDDED_OPTIONS") is not None:
            self.embedded_options = app.config.get("WEAVIATE_EMBEDDED_OPTIONS")

        if app.config.get("WEAVIATE_API_KEY") is not None:
            self.auth_client_secret = Auth.api_key(
                app.config.get("WEAVIATE_API_KEY")
            )
        elif (
            app.config.get("WEAVIATE_USERNAME") is not None
            and app.config.get("WEAVIATE_PASSWORD") is not None
        ):
            self.auth_client_secret = Auth.client_password(
                username=app.config.get("WEAVIATE_USERNAME"),
                password=app.config.get("WEAVIATE_PASSWORD"),
            )
        elif app.config.get("WEAVIATE_ACCESS_TOKEN") is not None:
            self.auth_client_secret = Auth.bearer_token(
                access_token=app.config.get("WEAVIATE_ACCESS_TOKEN")
            )
        elif app.config.get("WEAVIATE_AUTH_CLIENT_SECRET") is not None:
            self.auth_client_secret = app.config.get("WEAVIATE_AUTH_CLIENT_SECRET")

        if app.config.get("WEAVIATE_ADDITIONAL_HEADERS") is not None:
            self.additional_headers = app.config.get("WEAVIATE_ADDITIONAL_HEADERS")
        if app.config.get("WEAVIATE_ADDITIONAL_CONFIG") is not None:
            self.additional_config = app.config.get("WEAVIATE_ADDITIONAL_CONFIG")
        if app.config.get("WEAVIATE_SKIP_INIT_CHECKS") is not None:
            self.skip_init_checks = app.config.get("WEAVIATE_SKIP_INIT_CHECKS")
        self._client = WeaviateClient(**self.weaviate_config)

        # Store the WeaviateClient instance in the app context
        if not hasattr(app, "extensions"):
            app.extensions = {}
        app.extensions["weaviate"] = self

        @app.teardown_appcontext
        def close_connection(responese_or_exception):
            """
            Disconnect the Weaviate client during app context teardown.

            :param responese_or_exception:
            """
            if hasattr(self, "_client"):
                self._client.close()
            return responese_or_exception

        return app

    @property
    def client(self) -> WeaviateClient:
        """
        Lazily connect the WeaviateClient when it's first accessed.

        :return: The WeaviateClient instance.
        :rtype: WeaviateClient
        """
        if not hasattr(self, "_client") or self._client is None:
            self._client = WeaviateClient(**self.weaviate_config)
        if self._client.is_connected() is False:
            try:
                self._client.connect()
            except WeaviateStartUpError as e:
                raise Exception("Failed to connect to Weaviate server") from e
        return self._client

    @property
    def weaviate_config(self):
        # Define weaviate_config as a property
        if has_app_context():
            if any(
                x is not None
                for x in [
                    current_app.config.get("WEAVIATE_HTTP_HOST"),
                    current_app.config.get("WEAVIATE_HTTP_PORT"),
                ]
            ):
                self.connection_params = ConnectionParams.from_params(
                    http_host=current_app.config.get("WEAVIATE_HTTP_HOST", "localhost"),
                    http_port=current_app.config.get("WEAVIATE_HTTP_PORT", 80),
                    http_secure=current_app.config.get("WEAVIATE_HTTP_SECURE", False),
                    grpc_host=current_app.config.get("WEAVIATE_GRPC_HOST", "localhost"),
                    grpc_port=current_app.config.get("WEAVIATE_GRPC_PORT", 50051),
                    grpc_secure=current_app.config.get("WEAVIATE_GRPC_SECURE", False),
                )
                self.embedded_options = None
            elif current_app.config.get("WEAVIATE_CONNECTION_PARAMS") is not None:
                self.connection_params = current_app.config.get(
                    "WEAVIATE_CONNECTION_PARAMS"
                )
                self.embedded_options = None
            elif current_app.config.get("WEAVIATE_EMBEDDED_OPTIONS") is not None:
                self.embedded_options = current_app.config.get("WEAVIATE_EMBEDDED_OPTIONS")

            if current_app.config.get("WEAVIATE_API_KEY") is not None:
                self.auth_client_secret = AuthApiKey(
                    api_key=current_app.config.get("WEAVIATE_API_KEY")
                )
            elif (
                current_app.config.get("WEAVIATE_USERNAME") is not None
                and current_app.config.get("WEAVIATE_PASSWORD") is not None
            ):
                self.auth_client_secret = AuthClientPassword(
                    username=current_app.config.get("WEAVIATE_USERNAME"),
                    password=current_app.config.get("WEAVIATE_PASSWORD"),
                )
            elif current_app.config.get("WEAVIATE_ACCESS_TOKEN") is not None:
                self.auth_client_secret = AuthBearerToken(
                    access_token=current_app.config.get("WEAVIATE_ACCESS_TOKEN")
                )

            if current_app.config.get("WEAVIATE_ADDITIONAL_HEADERS") is not None:
                self.additional_headers = current_app.config.get(
                    "WEAVIATE_ADDITIONAL_HEADERS"
                )
            if current_app.config.get("WEAVIATE_ADDITIONAL_CONFIG") is not None:
                self.additional_config = current_app.config.get(
                    "WEAVIATE_ADDITIONAL_CONFIG"
                )
            if current_app.config.get("WEAVIATE_SKIP_INIT_CHECKS") is not None:
                self.skip_init_checks = current_app.config.get(
                    "WEAVIATE_SKIP_INIT_CHECKS"
                )
        return {
            "connection_params": self.connection_params,
            "embedded_options": self.embedded_options,
            "auth_client_secret": self.auth_client_secret,
            "additional_headers": self.additional_headers,
            "additional_config": self.additional_config,
            "skip_init_checks": self.skip_init_checks,
        }
