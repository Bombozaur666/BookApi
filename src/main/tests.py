import pytest


def test_no_content(client):
    resp = client.get('/')
    assert resp.status_code == 200
