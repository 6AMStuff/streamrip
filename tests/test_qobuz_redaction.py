"""Tests for the redaction of secrets in the Qobuz client logs."""

from streamrip.client.qobuz import mask_secret, redact_params


def test_mask_secret_hides_value():
    assert mask_secret("supersecret") == "*" * len("supersecret")


def test_redact_params_masks_sensitive_values():
    params = {
        "app_id": "12345",
        "user_auth_token": "abcdefghij",
        "password": "hunter2",
        "limit": 500,
    }
    redacted = redact_params(params)

    assert redacted["app_id"] == "12345"
    assert redacted["limit"] == 500
    assert redacted["user_auth_token"] == "*" * len("abcdefghij")
    assert redacted["password"] == "*" * len("hunter2")


def test_redact_params_does_not_mutate_input():
    params = {"user_auth_token": "abcdefghij"}
    redact_params(params)

    assert params["user_auth_token"] == "abcdefghij"


def test_redact_params_without_sensitive_keys():
    params = {"app_id": "12345", "track_id": "42"}
    assert redact_params(params) == params


def test_redact_params_recurses_into_nested_structures():
    params = {
        "user": {"credential": {"parameters": {"secret": "xyz"}, "id": 1}},
        "items": [{"token": "t"}, 2],
    }
    redacted = redact_params(params)

    assert redacted["user"]["credential"]["parameters"]["secret"] == "***"
    assert redacted["user"]["credential"]["id"] == 1
    assert redacted["items"][0]["token"] == "*"
    assert redacted["items"][1] == 2


def test_redact_params_with_non_dict():
    assert redact_params("not a dict") == "not a dict"
