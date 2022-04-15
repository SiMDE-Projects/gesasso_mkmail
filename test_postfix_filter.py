import pytest

from postfix_filter import encoded_words_to_text


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
