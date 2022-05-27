import pytest
import os

from postfix_filter import encoded_words_to_text, is_simde_email


@pytest.mark.parametrize(
    "encoded,decoded",
    [
        (
            "=?UTF-8?Q?C=C3=A9sar_Richard?= <cesar.richard2@gmail.com>",
            "César_Richard <cesar.richard2@gmail.com>",
        ),
        ("cesar.richard2@gmail.com", "cesar.richard2@gmail.com"),
        ("Bob Dylan <bob.dylan@etu.utc.fr>", "Bob Dylan <bob.dylan@etu.utc.fr>"),
        ("=?utf-8?Q?=C3=A9?=", "é"),
    ],
)
def test_encoded_words_to_text(encoded, decoded):
    assert encoded_words_to_text(encoded) == decoded


@pytest.mark.parametrize(
    "mail,force_handle_env,result",
    [
        ("cesar.richard@gmail.com", False, False),
        ("cesar.richard@utc.fr", False, False),
        ("simde@utc.fr", False, False),
        ("payutc@utc.fr", False, False),
        ("poleae@assos.utc.fr", False, False),
        ("poleae-bureau@assos.utc.fr", False, False),
        ("simde@assos.utc.fr", False, True),
        ("simde-bureau@assos.utc.fr", False, True),
        ("payutc@assos.utc.fr", False, True),
        ("payutc-bureau@assos.utc.fr", False, True),
        ("woolly@assos.utc.fr", False, True),
        ("cesar.richard@gmail.com", True, True),
        ("cesar.richard@utc.fr", True, True),
        ("simde@utc.fr", True, True),
        ("payutc@utc.fr", True, True),
        ("poleae@assos.utc.fr", True, True),
        ("poleae-bureau@assos.utc.fr", True, True),
        ("simde@assos.utc.fr", True, True),
        ("simde-bureau@assos.utc.fr", True, True),
        ("payutc@assos.utc.fr", True, True),
        ("payutc-bureau@assos.utc.fr", True, True),
        ("woolly@assos.utc.fr", True, True),
    ],
)
def test_is_simde_email(mail: str, force_handle_env: bool, result: bool):
    os.environ["HANDLE_ALL_MAILS"] = "True" if force_handle_env else "False"
    assert is_simde_email(mail) == result
