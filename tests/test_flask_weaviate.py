import pytest
from flask import Flask
from weaviate import WeaviateClient

from flask_weaviate import FlaskWeaviate


@pytest.fixture
def app():
    return Flask(__name__)


def test_init_without_app():
    weaviate = FlaskWeaviate()
    assert isinstance(weaviate.client, WeaviateClient)

    assert weaviate.client.is_connected()


def test_init_with_app(app):
    weaviate = FlaskWeaviate(app=app)

    assert isinstance(weaviate.client, WeaviateClient)
    assert weaviate.client.is_connected()


def test_init_app(app):
    weaviate = FlaskWeaviate()
    weaviate.init_app(app)

    assert isinstance(weaviate.client, WeaviateClient)
    assert weaviate.client.is_connected()


def test_weaviate_client_property(app):
    weaviate = FlaskWeaviate(app=app)
    weaviate.init_app(app)

    assert isinstance(weaviate.client, WeaviateClient)
    assert weaviate.client.is_connected()
