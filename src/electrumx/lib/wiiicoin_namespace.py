# Copyright (c) 2026, W3Vault Limited
# Licensed under the MIT licence.

"""Wiiicoin namespace script parsing and index helpers."""

from dataclasses import dataclass

from electrumx.lib.hash import Base58, HASHX_LEN, sha256


OP_NAMESPACE = 0xD0
OP_PUT = 0xD1
OP_DELETE = 0xD2

OP_PUSHDATA1 = 0x4C
OP_PUSHDATA2 = 0x4D
OP_PUSHDATA4 = 0x4E
OP_2DROP = 0x6D
OP_DROP = 0x75
OP_RETURN = 0x6A

NAMESPACE_PREFIX = 0x35
ROOT_NAMESPACE_KEY = b"\x01_KEVA_NS_"


@dataclass(frozen=True, slots=True)
class NamespaceScript:
    """Decoded Wiiicoin namespace prefix and its trailing ownership script."""

    operation: int
    namespace: bytes
    key: bytes
    value: bytes | None
    address_script: bytes

    @property
    def namespace_id(self) -> str:
        return Base58.encode_check(self.namespace)

    @property
    def operation_name(self) -> str:
        return {
            OP_NAMESPACE: "REG",
            OP_PUT: "PUT",
            OP_DELETE: "DEL",
        }[self.operation]


def _read_push_data(script: bytes, cursor: int) -> tuple[bytes, int]:
    if cursor >= len(script):
        raise ValueError("missing pushed data")

    opcode = script[cursor]
    cursor += 1

    if opcode <= 0x4B:
        size = opcode
    elif opcode == OP_PUSHDATA1:
        if cursor + 1 > len(script):
            raise ValueError("truncated OP_PUSHDATA1")
        size = script[cursor]
        cursor += 1
    elif opcode == OP_PUSHDATA2:
        if cursor + 2 > len(script):
            raise ValueError("truncated OP_PUSHDATA2")
        size = int.from_bytes(script[cursor:cursor + 2], "little")
        cursor += 2
    elif opcode == OP_PUSHDATA4:
        if cursor + 4 > len(script):
            raise ValueError("truncated OP_PUSHDATA4")
        size = int.from_bytes(script[cursor:cursor + 4], "little")
        cursor += 4
    else:
        raise ValueError("expected a data push")

    end = cursor + size
    if end > len(script):
        raise ValueError("truncated pushed data")
    return script[cursor:end], end


def push_data(value: bytes) -> bytes:
    """Return the minimally encoded Bitcoin Script push for *value*."""

    size = len(value)
    if size <= 0x4B:
        return bytes((size,)) + value
    if size <= 0xFF:
        return bytes((OP_PUSHDATA1, size)) + value
    if size <= 0xFFFF:
        return bytes((OP_PUSHDATA2,)) + size.to_bytes(2, "little") + value
    return bytes((OP_PUSHDATA4,)) + size.to_bytes(4, "little") + value


def parse_namespace_script(script: bytes) -> NamespaceScript | None:
    """Decode a Wiiicoin namespace output, returning ``None`` when not applicable."""

    if not script or script[0] not in (OP_NAMESPACE, OP_PUT, OP_DELETE):
        return None

    try:
        operation = script[0]
        namespace, cursor = _read_push_data(script, 1)
        key, cursor = _read_push_data(script, cursor)

        value = None
        if operation == OP_PUT:
            value, cursor = _read_push_data(script, cursor)

        if cursor >= len(script) or script[cursor] != OP_2DROP:
            return None
        cursor += 1

        if operation == OP_PUT:
            if cursor >= len(script) or script[cursor] != OP_DROP:
                return None
            cursor += 1

        if len(namespace) != 21 or namespace[0] != NAMESPACE_PREFIX:
            return None

        address_script = script[cursor:]
        if not address_script:
            return None

        return NamespaceScript(
            operation=operation,
            namespace=namespace,
            key=key,
            value=value,
            address_script=address_script,
        )
    except (IndexError, ValueError):
        return None


def build_namespace_index_script(index_name: bytes) -> bytes:
    """Build the synthetic script used by ElectrumX namespace history indexes."""

    return b"".join((
        bytes((OP_PUT,)),
        push_data(index_name),
        push_data(b""),
        bytes((OP_2DROP, OP_DROP, OP_RETURN)),
    ))


def namespace_index_hashX(namespace: bytes) -> bytes:
    """Return the generic per-namespace history hashX."""

    return sha256(build_namespace_index_script(namespace))[:HASHX_LEN]


def namespace_key_index_hashX(namespace_script: NamespaceScript) -> bytes:
    """Return the namespace/key history hashX for an operation."""

    if namespace_script.operation == OP_NAMESPACE:
        index_name = namespace_script.namespace + ROOT_NAMESPACE_KEY
    else:
        index_name = namespace_script.namespace + namespace_script.key
    return sha256(build_namespace_index_script(index_name))[:HASHX_LEN]
