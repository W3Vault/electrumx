# Copyright (c) 2026, W3Vault Limited
# Licensed under the MIT licence.

"""Wiiicoin network definition for ElectrumX.

This module is imported by :mod:`electrumx` so the class is registered as a
subclass of ``Coin`` and can be selected with ``COIN=Wiiicoin`` and
``NET=main``.
"""

from electrumx.lib.coins import Coin
from electrumx.lib.tx import DeserializerSegWit


class Wiiicoin(Coin):
    """Wiiicoin main network."""

    NAME = "Wiiicoin"
    SHORTNAME = "WIII"
    NET = "main"

    # Wiiicoin blocks use an 80-byte Bitcoin-style header, followed by a
    # one-byte blob-size field and a 76-byte CryptoNight header blob.
    BASIC_HEADER_SIZE = 157

    P2PKH_VERBYTE = bytes.fromhex("87")
    P2SH_VERBYTES = (bytes.fromhex("7d"),)
    GENESIS_HASH = (
        "000000b6342a3f29e384a67490086d5d"
        "d987f6947a4308d56a893294b96fa146"
    )

    DESERIALIZER = DeserializerSegWit
    RPC_PORT = 8688
    REORG_LIMIT = 800

    TX_COUNT = 1
    TX_COUNT_HEIGHT = 1
    TX_PER_BLOCK = 1

    PEER_DEFAULT_PORTS = {"t": "50001", "s": "50002"}
    PEERS = []

    @classmethod
    def header_hash_rev(cls, header: bytes) -> bytes:
        """Return the Wiiicoin CryptoNight header hash.

        Wiiicoin hashes the 76-byte CryptoNight blob beginning immediately
        after the Bitcoin-style header and its one-byte blob-size field.
        """
        try:
            import pycryptonight
        except ImportError as exc:
            raise RuntimeError(
                "Wiiicoin support requires the optional 'pycryptonight' "
                "package"
            ) from exc

        if len(header) != cls.BASIC_HEADER_SIZE:
            raise ValueError(
                f"Wiiicoin header must be {cls.BASIC_HEADER_SIZE} bytes, "
                f"got {len(header)}"
            )
        return pycryptonight.cn_fast_hash(header[81:])
