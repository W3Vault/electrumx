# Tests for Wiiicoin namespace scripts and indexes.

from electrumx.lib.coins_wiiicoin import Wiiicoin
from electrumx.lib.hash import sha256
from electrumx.lib.wiiicoin_namespace import (
    OP_DELETE,
    OP_NAMESPACE,
    OP_PUT,
    ROOT_NAMESPACE_KEY,
    build_namespace_index_script,
    namespace_index_hashX,
    namespace_key_index_hashX,
    parse_namespace_script,
    push_data,
)


NAMESPACE = bytes((0x35,)) + bytes(range(1, 21))
OWNER_SCRIPT = bytes.fromhex(
    "a914000102030405060708090a0b0c0d0e0f1011121387"
)


def namespace_script(operation, key, value=None):
    parts = [bytes((operation,)), push_data(NAMESPACE), push_data(key)]
    if operation == OP_PUT:
        parts.append(push_data(value or b""))
        parts.append(bytes((0x6D, 0x75)))
    else:
        parts.append(bytes((0x6D,)))
    parts.append(OWNER_SCRIPT)
    return b"".join(parts)


def test_parse_namespace_creation_and_owner_index():
    script = namespace_script(OP_NAMESPACE, b"Mark")
    parsed = parse_namespace_script(script)

    assert parsed is not None
    assert parsed.operation == OP_NAMESPACE
    assert parsed.namespace == NAMESPACE
    assert parsed.key == b"Mark"
    assert parsed.value is None
    assert parsed.address_script == OWNER_SCRIPT
    assert Wiiicoin.hashX_from_script(script) == sha256(OWNER_SCRIPT)[:11]


def test_parse_namespace_put_and_delete():
    put = parse_namespace_script(namespace_script(OP_PUT, b"bio", b"Founder"))
    delete = parse_namespace_script(namespace_script(OP_DELETE, b"bio"))

    assert put is not None
    assert put.key == b"bio"
    assert put.value == b"Founder"
    assert put.operation_name == "PUT"

    assert delete is not None
    assert delete.key == b"bio"
    assert delete.value is None
    assert delete.operation_name == "DEL"


def test_namespace_indexes_match_wallet_scripthashes():
    creation = parse_namespace_script(namespace_script(OP_NAMESPACE, b"Mark"))
    assert creation is not None

    generic_script = build_namespace_index_script(NAMESPACE)
    root_script = build_namespace_index_script(NAMESPACE + ROOT_NAMESPACE_KEY)

    assert sha256(generic_script)[::-1].hex() == (
        "553f31990860da5ab7e8e158bec314d571e95d3563fdbdafc87f9064fc1fa31d"
    )
    assert sha256(root_script)[::-1].hex() == (
        "4176d32a3c6748affe1e294c33a2a8ee17de4df3fe9ced58ec81f4156b6125a5"
    )
    assert namespace_index_hashX(NAMESPACE) == sha256(generic_script)[:11]
    assert namespace_key_index_hashX(creation) == sha256(root_script)[:11]


def test_invalid_namespace_script_is_not_parsed():
    assert parse_namespace_script(b"") is None
    assert parse_namespace_script(b"\xd1\x01\x35") is None
    assert parse_namespace_script(b"\x6a") is None
