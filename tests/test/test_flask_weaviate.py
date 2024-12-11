import pytest
from faker import Faker
from httpx import ConnectError

fake = Faker()


@pytest.fixture
def app():
    from flask import Flask, jsonify
    app = Flask(__name__)
    with app.app_context():
        yield app  # The teardown code will be executed after the test

    # Teardown code (e.g., closing database connections, cleaning up resources)
    # Add your teardown logic here


@pytest.fixture
def client_with_weaviate(app):
    from flask_weaviate import FlaskWeaviate
    weaviate = FlaskWeaviate()
    weaviate.init_app(app)

    @app.route('/search', methods=['GET'])
    def search_endpoint():
        from flask import jsonify
        assert weaviate.client.is_connected()
        weaviate.client.collections.delete_all()
        coll = weaviate.client.collections.create('test')
        with coll.batch.dynamic() as batch:
            batch.add_object({"text": "testing this"})

        resp = coll.query.bm25(query="testing this")
        # Replace this with your actual search logic
        result = {'message': resp.objects[0].properties['text']}
        return jsonify(result), 200

    # Create a test client for the Flask app
    return app.test_client()


def test_init_without_app():
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    weaviate = FlaskWeaviate()

    with pytest.raises(RuntimeError) as e:
        assert isinstance(weaviate.client, WeaviateClient)

    e.value.message = "Working outside of application context"


def test_init_with_app(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    weaviate = FlaskWeaviate(app=app)

    assert isinstance(weaviate.client, WeaviateClient)
    assert weaviate.client.is_connected()


def test_init_app(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    weaviate = FlaskWeaviate()
    weaviate.init_app(app)

    assert isinstance(weaviate.client, WeaviateClient)
    assert weaviate.client.is_connected()


def test_weaviate_client_property(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    weaviate = FlaskWeaviate(app=app)
    weaviate.init_app(app)

    assert isinstance(weaviate.client, WeaviateClient)
    assert weaviate.client.is_connected()


def test_init_app_no_extensions(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    del app.extensions
    weaviate = FlaskWeaviate()
    weaviate.init_app(app)

    assert isinstance(weaviate.client, WeaviateClient)
    assert weaviate.client.is_connected()


def test_weaviate_search_endpoint(client_with_weaviate):
    client = client_with_weaviate
    # Your test logic here
    response = client.get('/search')

    # Example assertion
    assert response.status_code == 200
    assert response.json['message'] == 'testing this'


def test_app_config_http(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    from weaviate.connect import ConnectionParams

    weaviate = FlaskWeaviate()
    app.config['WEAVIATE_HTTP_HOST'] = fake.word()
    app.config['WEAVIATE_HTTP_PORT'] = fake.pyint(min_value=1000, max_value=65535)
    app.config['WEAVIATE_HTTP_SECURE'] = True
    app.config['WEAVIATE_GRPC_HOST'] = fake.word()
    app.config['WEAVIATE_GRPC_PORT'] = fake.pyint(min_value=1000, max_value=65535)
    app.config['WEAVIATE_GRPC_SECURE'] = True
    weaviate.init_app(app)

    assert weaviate.connection_params == ConnectionParams.from_params(
        http_host=app.config['WEAVIATE_HTTP_HOST'],
        http_port=app.config['WEAVIATE_HTTP_PORT'],
        http_secure=app.config['WEAVIATE_HTTP_SECURE'],
        grpc_host=app.config['WEAVIATE_GRPC_HOST'],
        grpc_port=app.config['WEAVIATE_GRPC_PORT'],
        grpc_secure=app.config['WEAVIATE_GRPC_SECURE'],
    )

    with pytest.raises(ConnectError):
        isinstance(weaviate.client, WeaviateClient)


def test_app_config_connection_params(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    from weaviate.connect import ConnectionParams

    weaviate = FlaskWeaviate()
    app.config['WEAVIATE_CONNECTION_PARAMS'] = ConnectionParams.from_params(
        http_host="localhost",
        http_port=fake.pyint(min_value=1000, max_value=65535),
        http_secure=True,
        grpc_host="localhost",
        grpc_port=fake.pyint(min_value=1000, max_value=65535),
        grpc_secure=True
    )
    weaviate.init_app(app)

    assert weaviate.connection_params == app.config['WEAVIATE_CONNECTION_PARAMS']

    with pytest.raises(ConnectError):
        isinstance(weaviate.client, WeaviateClient)


def test_app_config_embedded_options(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    from weaviate.embedded import EmbeddedOptions

    weaviate = FlaskWeaviate()
    app.config['WEAVIATE_EMBEDDED_OPTIONS'] = EmbeddedOptions()
    weaviate.init_app(app)

    assert weaviate.embedded_options == EmbeddedOptions()

    isinstance(weaviate.client, WeaviateClient)
    assert weaviate.client.is_connected()


def test_app_config_api_key(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    from weaviate.auth import Auth
    from weaviate.exceptions import UnexpectedStatusCodeError

    weaviate = FlaskWeaviate()
    app.config['WEAVIATE_API_KEY'] = fake.word()
    weaviate.init_app(app)

    assert weaviate.auth_client_secret == Auth.api_key(app.config['WEAVIATE_API_KEY'])

    with pytest.raises(UnexpectedStatusCodeError):
        isinstance(weaviate.client, WeaviateClient)


def test_app_config_username_password(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    from weaviate.auth import Auth

    weaviate = FlaskWeaviate()
    app.config['WEAVIATE_USERNAME'] = fake.word()
    app.config['WEAVIATE_PASSWORD'] = fake.password()
    weaviate.init_app(app)

    assert weaviate.auth_client_secret == Auth.client_password(
        username=app.config['WEAVIATE_USERNAME'],
        password=app.config['WEAVIATE_PASSWORD']
    )

    # with pytest.raises(UnexpectedStatusCodeError):
    isinstance(weaviate.client, WeaviateClient)


def test_app_config_access_token(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    from weaviate.auth import Auth

    weaviate = FlaskWeaviate()
    app.config['WEAVIATE_ACCESS_TOKEN'] = fake.word()
    weaviate.init_app(app)

    assert weaviate.auth_client_secret == Auth.bearer_token(app.config['WEAVIATE_ACCESS_TOKEN'])

    isinstance(weaviate.client, WeaviateClient)


def test_app_config_auth_client_secret(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    from weaviate.auth import Auth
    from weaviate.exceptions import UnexpectedStatusCodeError

    weaviate = FlaskWeaviate()
    app.config['WEAVIATE_AUTH_CLIENT_SECRET'] = Auth.api_key(fake.word())
    weaviate.init_app(app)

    assert weaviate.auth_client_secret == app.config['WEAVIATE_AUTH_CLIENT_SECRET']

    with pytest.raises(UnexpectedStatusCodeError):
        isinstance(weaviate.client, WeaviateClient)


def test_app_config_additional_params(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    from weaviate.config import AdditionalConfig
    from weaviate.exceptions import UnexpectedStatusCodeError

    weaviate = FlaskWeaviate()
    app.config['WEAVIATE_ADDITIONAL_HEADERS'] = dict(Authorization=f"Bearer {fake.password()}")
    app.config['WEAVIATE_ADDITIONAL_CONFIG'] = AdditionalConfig(timeout=(5, 10))
    app.config['WEAVIATE_SKIP_INIT_CHECKS'] = True
    weaviate.init_app(app)

    assert weaviate.additional_config.timeout == (5, 10)
    assert weaviate.additional_headers == app.config['WEAVIATE_ADDITIONAL_HEADERS']
    assert weaviate.skip_init_checks

    with pytest.raises(UnexpectedStatusCodeError):
        isinstance(weaviate.client, WeaviateClient)


def test_init_with_port(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient

    weaviate = FlaskWeaviate(http_port=fake.pyint(min_value=1000, max_value=65535))
    weaviate.init_app(app)

    with pytest.raises(ConnectError):
        isinstance(weaviate.client, WeaviateClient)


def test_init_with_connection_params(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    from weaviate.connect import ConnectionParams

    weaviate = FlaskWeaviate(connection_params=ConnectionParams.from_params(
        http_host="localhost",
        http_port=fake.pyint(min_value=1000, max_value=65535),
        http_secure=True,
        grpc_host="localhost",
        grpc_port=fake.pyint(min_value=1000, max_value=65535),
        grpc_secure=True
    ))
    weaviate.init_app(app)

    with pytest.raises(ConnectError):
        isinstance(weaviate.client, WeaviateClient)


def test_init_with_embedded_params(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    from weaviate.embedded import EmbeddedOptions

    weaviate = FlaskWeaviate(embedded_options=EmbeddedOptions())
    weaviate.init_app(app)

    isinstance(weaviate.client, WeaviateClient)
    assert weaviate.client.is_connected()


def test_init_with_api_key(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    from weaviate.exceptions import UnexpectedStatusCodeError

    weaviate = FlaskWeaviate(api_key=fake.word())
    weaviate.init_app(app)

    with pytest.raises(UnexpectedStatusCodeError):
        isinstance(weaviate.client, WeaviateClient)


def test_init_with_username_password(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient

    weaviate = FlaskWeaviate(username=fake.word(), password=fake.password())
    weaviate.init_app(app)

    # with pytest.raises(UnexpectedStatusCodeError):
    isinstance(weaviate.client, WeaviateClient)


def test_init_with_access_token(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient

    weaviate = FlaskWeaviate(access_token=fake.word())
    weaviate.init_app(app)

    isinstance(weaviate.client, WeaviateClient)


def test_init_with_auth_client_secret(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    from weaviate.auth import Auth
    from weaviate.exceptions import UnexpectedStatusCodeError

    weaviate = FlaskWeaviate(auth_client_secret=Auth.api_key(fake.word()))
    weaviate.init_app(app)

    with pytest.raises(UnexpectedStatusCodeError):
        isinstance(weaviate.client, WeaviateClient)


def test_init_with_none_connection_embedded(app):
    with pytest.raises(ValueError) as e:
        from flask_weaviate import FlaskWeaviate
        FlaskWeaviate(connection_params=None, embedded_options=None)
    assert str(e.value) == "Both connection_params and embedded_options cannot be None."


def test_init_with_additional_params(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate import WeaviateClient
    from weaviate.config import AdditionalConfig
    from weaviate.exceptions import UnexpectedStatusCodeError

    weaviate = FlaskWeaviate(
        additional_headers=dict(Authorization=f"Bearer {fake.password()}"),
        additional_config=AdditionalConfig(timeout=(5, 10)),
        skip_init_checks=True,
    )
    weaviate.init_app(app)

    with pytest.raises(UnexpectedStatusCodeError):
        isinstance(weaviate.client, WeaviateClient)


def test_init_lazy_with_app_config_embedded(app):
    from flask_weaviate import FlaskWeaviate
    from weaviate.config import AdditionalConfig
    from weaviate.embedded import EmbeddedOptions

    embedded_options = EmbeddedOptions()
    embedded_options.port = fake.pyint(min_value=1000, max_value=65535)
    app.config['WEAVIATE_EMBEDDED_OPTIONS'] = embedded_options
    app.config['WEAVIATE_ADDITIONAL_HEADERS'] = dict(Authorization=f"Bearer {fake.password()}")
    app.config['WEAVIATE_ADDITIONAL_CONFIG'] = AdditionalConfig(timeout=(5, 10))
    app.config['WEAVIATE_SKIP_INIT_CHECKS'] = True
    app.config['WEAVIATE_ACCESS_TOKEN'] = fake.password()

    weaviate = FlaskWeaviate()

    @app.route('/search', methods=['GET'])
    def search_endpoint():
        from flask import jsonify
        from weaviate.auth import Auth
        from weaviate.connect.base import _Timeout

        assert weaviate.client.is_connected()

        # test if the client is lazily instanced with the app options
        assert weaviate._client._connection.embedded_db.options.port == embedded_options.port
        assert weaviate._client._WeaviateClient__skip_init_checks == app.config['WEAVIATE_SKIP_INIT_CHECKS']
        assert weaviate._client._connection.additional_headers == app.config['WEAVIATE_ADDITIONAL_HEADERS']
        assert weaviate._client._connection.timeout_config == _Timeout(connect=5, read=10)
        assert weaviate._client._connection._Connection__auth == Auth.bearer_token(app.config['WEAVIATE_ACCESS_TOKEN'])

        return jsonify({"result": "ok"}), 200

    client = app.test_client()

    response = client.get('/search')

    # Example assertion
    assert response.status_code == 200
    assert response.json['result'] == 'ok'


def test_init_lazy_with_app_config_connection_params(app):
    from weaviate.connect import ConnectionParams

    app.config['WEAVIATE_CONNECTION_PARAMS'] = ConnectionParams.from_params(
        http_host="localhost",
        http_port=fake.pyint(min_value=1000, max_value=65535),
        http_secure=True,
        grpc_host="localhost",
        grpc_port=fake.pyint(min_value=1000, max_value=65535),
        grpc_secure=True
    )
    app.config['WEAVIATE_API_KEY'] = fake.password()

    from flask_weaviate import FlaskWeaviate
    weaviate = FlaskWeaviate()

    @app.route('/search', methods=['GET'])
    def search_endpoint():
        from flask import jsonify
        from weaviate.auth import Auth

        with pytest.raises(Exception) as e:
            weaviate.client.is_connected()

        assert str(e.value) == "Failed to connect to Weaviate server"
        # test if the client is lazily instanced with the app options
        assert weaviate._client._connection._Connection__auth == Auth.api_key(app.config['WEAVIATE_API_KEY'])
        assert weaviate._client._connection._connection_params == app.config['WEAVIATE_CONNECTION_PARAMS']

        return jsonify({"result": "ok"}), 200

    client = app.test_client()

    response = client.get('/search')

    # Example assertion
    assert response.status_code == 200
    assert response.json['result'] == 'ok'

def test_init_lazy_with_app_config_http_params(app):
    app.config['WEAVIATE_HTTP_HOST'] = fake.word()
    app.config['WEAVIATE_HTTP_PORT'] = fake.pyint(min_value=1000, max_value=65535)
    app.config['WEAVIATE_HTTP_SECURE'] = True
    app.config['WEAVIATE_GRPC_HOST'] = fake.word()
    app.config['WEAVIATE_GRPC_PORT'] = fake.pyint(min_value=1000, max_value=65535)
    app.config['WEAVIATE_GRPC_SECURE'] = True
    app.config['WEAVIATE_USERNAME'] = fake.word()
    app.config['WEAVIATE_PASSWORD'] = fake.password()

    from flask_weaviate import FlaskWeaviate
    weaviate = FlaskWeaviate()

    @app.route('/search', methods=['GET'])
    def search_endpoint():
        from flask import jsonify
        from weaviate.auth import Auth
        from weaviate.connect import ConnectionParams

        with pytest.raises(ConnectError):
            weaviate.client.is_connected()

        # test if the client is lazily instanced with the app options
        assert weaviate._client._connection._Connection__auth == Auth.client_password(
            username=app.config['WEAVIATE_USERNAME'],
            password=app.config['WEAVIATE_PASSWORD']
        )
        assert weaviate._client._connection._connection_params == ConnectionParams.from_params(
            http_host=app.config['WEAVIATE_HTTP_HOST'],
            http_port=app.config['WEAVIATE_HTTP_PORT'],
            http_secure=app.config['WEAVIATE_HTTP_SECURE'],
            grpc_host=app.config['WEAVIATE_GRPC_HOST'],
            grpc_port=app.config['WEAVIATE_GRPC_PORT'],
            grpc_secure=app.config['WEAVIATE_GRPC_SECURE'],
        )

        return jsonify({"result": "ok"}), 200

    client = app.test_client()

    response = client.get('/search')

    # Example assertion
    assert response.status_code == 200
    assert response.json['result'] == 'ok'
