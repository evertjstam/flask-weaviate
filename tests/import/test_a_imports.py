import pytest


def test_import_failure_flask(monkeypatch):
    import sys
    with monkeypatch.context() as m:
        monkeypatch.setitem(sys.modules, "flask", None)

        with pytest.raises(ImportError) as e:
            from flask_weaviate import FlaskWeaviate

        assert str(e.value) == "Flask-Weaviate requires the 'Flask' library. Install it using 'pip install Flask'."


def test_import_failure_weaviate(monkeypatch):
    import sys
    with monkeypatch.context() as m:
        monkeypatch.setitem(sys.modules, "weaviate", None)

        with pytest.raises(ImportError) as e:
            from flask_weaviate import FlaskWeaviate

        assert str(
            e.value) == "Flask-Weaviate requires the 'weaviate_client' library. Install it using 'pip install weaviate'."
