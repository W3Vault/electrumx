# Copyright (c) 2026, W3Vault Limited
# Licensed under the MIT licence.

"""Wiiicoin network definition for ElectrumX.

This module is imported by :mod:`electrumx` so the class is registered as a
subclass of ``Coin`` and can be selected with ``COIN=Wiiicoin`` and
``NET=main``.
"""

from Cryptodome.Hash import keccak

from electrumx.lib.coins import Coin
from electrumx.lib.tx import DeserializerSegWit


class Wiiicoin(Coin):
    """Wiiicoin main network."""

    NAME = "Wiiicoin"
    SHORTNAME = "WIII"
    NET = "main"

    # Wiiicoin serialises an 80-byte Bitcoin-style header followed by a
    # compact-size-prefixed CryptoNote header blob. The blob length can vary
    # from block to block, so offsets must be recorded dynamically.
    BASIC_HEADER_SIZE = 81
    STATIC_BLOCK_HEADERS = False

    P2PKH_VERBYTE = bytes.fromhex("87")
    P2SH_VERBYTES = (bytes.fromhex("7d"),)
    GENESIS_HASH = (
        "000000b6342a3f29e384a67490086d5d"
        "d987f6947a4308d56a893294b96fa146"
    )

    DESERIALIZER = DeserializerSegWit
    RPC_PORT = 8868
    REORG_LIMIT = 800

    TX_COUNT = 1
    TX_COUNT_HEIGHT = 1
    TX_PER_BLOCK = 1

    PEER_DEFAULT_PORTS = {"t": "50001", "s": "50002"}
    PEERS = []

    @classmethod
    def max_fetch_blocks(cls, height: int) -> int:
        """Fetch one block at a time from the Wiiicoin daemon.

        The Wiiicoin daemon can return batched ``getblock`` responses out of
        request order. ElectrumX expects each returned batch to be ordered as
        a contiguous chain, so single-block fetching prevents deterministic
        prefetch resets.
        """
        return 1

    @classmethod
    def block_header(cls, block: bytes, height: int) -> bytes:
        """Return the variable-length Wiiicoin block header.

        Byte 80 stores the serialized CryptoNote blob length. The full header
        is therefore the 80-byte Bitcoin-style prefix, the one-byte length
        field, and the indicated blob.
        """
        if len(block) < cls.BASIC_HEADER_SIZE:
            raise ValueError(
                f"Wiiicoin block is too short for a header: {len(block)} bytes"
            )

        header_len = cls.BASIC_HEADER_SIZE + block[80]
        if len(block) < header_len:
            raise ValueError(
                f"Wiiicoin block declares a {header_len}-byte header, "
                f"but only {len(block)} bytes are available"
            )
        return block[:header_len]

    @classmethod
    def header_hash_rev(cls, header: bytes) -> bytes:
        """Return the Wiiicoin CryptoNight fast header hash.

        Wiiicoin applies Keccak-256 to the CryptoNote blob beginning
        immediately after the Bitcoin-style header and its one-byte blob-size
        field.
        """
        if len(header) < cls.BASIC_HEADER_SIZE:
            raise ValueError(
                f"Wiiicoin header must be at least {cls.BASIC_HEADER_SIZE} bytes, "
                f"got {len(header)}"
            )

        expected_len = cls.BASIC_HEADER_SIZE + header[80]
        if len(header) != expected_len:
            raise ValueError(
                f"Wiiicoin header length mismatch: declared {expected_len} bytes, "
                f"got {len(header)}"
            )

        hasher = keccak.new(digest_bits=256)
        hasher.update(header[81:])
        return hasher.digest()
