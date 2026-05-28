import pytest
from cryptography.exceptions import InvalidTag

from app.services.encryption import decrypt_field, derive_key, encrypt_field, generate_salt


def test_generate_salt_length():
    salt = generate_salt()
    assert len(salt) == 16


def test_generate_salt_unique():
    assert generate_salt() != generate_salt()


def test_derive_key_length():
    key = derive_key("password123", generate_salt())
    assert len(key) == 32


def test_derive_key_deterministic():
    salt = generate_salt()
    k1 = derive_key("password", salt)
    k2 = derive_key("password", salt)
    assert k1 == k2


def test_derive_key_different_passwords():
    salt = generate_salt()
    assert derive_key("password1", salt) != derive_key("password2", salt)


def test_derive_key_different_salts():
    assert derive_key("password", generate_salt()) != derive_key("password", generate_salt())


def test_encrypt_decrypt_roundtrip():
    key = derive_key("master", generate_salt())
    plaintext = "super-secret-password-123"
    blob = encrypt_field(plaintext, key)
    assert decrypt_field(blob, key) == plaintext


def test_encrypt_produces_different_blobs():
    key = derive_key("master", generate_salt())
    plaintext = "same text"
    assert encrypt_field(plaintext, key) != encrypt_field(plaintext, key)


def test_decrypt_wrong_key_raises():
    key1 = derive_key("correct", generate_salt())
    key2 = derive_key("wrong", generate_salt())
    blob = encrypt_field("secret", key1)
    with pytest.raises(InvalidTag):
        decrypt_field(blob, key2)


def test_encrypt_unicode():
    key = derive_key("密码", generate_salt())
    text = "这是一个中文密码！@#¥"
    assert decrypt_field(encrypt_field(text, key), key) == text


def test_encrypt_empty_string():
    key = derive_key("pwd", generate_salt())
    assert decrypt_field(encrypt_field("", key), key) == ""


def test_blob_contains_nonce():
    key = derive_key("pwd", generate_salt())
    blob = encrypt_field("data", key)
    assert len(blob) > 12  # nonce (12) + ciphertext
