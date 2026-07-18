# Copyright (c) 2026, W3Vault Limited
# Licensed under the MIT licence.

"""Wiiicoin namespace indexing and Electrum protocol handlers."""

import base64
from typing import Any, Sequence

from aiorpcx import RPCError

from electrumx.lib.hash import hash_to_hex_str
from electrumx.lib.tx import Tx
from electrumx.lib.wiiicoin_namespace import (
    NamespaceScript,
    namespace_index_hashX,
    namespace_key_index_hashX,
    parse_namespace_script,
)
from electrumx.server.block_processor import BlockProcessor
from electrumx.server.session import (
    BAD_REQUEST,
    ElectrumX,
    assert_txid_hum,
    scripthash_to_hashX,
)


MAX_NAMESPACE_INFO_TXS = 200


class WiiicoinBlockProcessor(BlockProcessor):
    """Add generic namespace and namespace/key histories to the address index."""

    def advance_txs_process_outputs(
            self,
            txs: Sequence[Tx],
            *,
            height: int,
    ) -> None:
        super().advance_txs_process_outputs(txs, height=height)

        tx_num_start = self.db.tx_counts[height - 1] if height > 0 else 0
        hashxs_by_tx: list[list[bytes]] = []

        for tx in txs:
            namespace_hashxs: set[bytes] = set()
            for txout in tx.outputs:
                namespace_script = parse_namespace_script(txout.pk_script)
                if namespace_script is None:
                    continue
                namespace_hashxs.add(
                    namespace_index_hashX(namespace_script.namespace)
                )
                namespace_hashxs.add(
                    namespace_key_index_hashX(namespace_script)
                )

            hashxs = sorted(namespace_hashxs)
            hashxs_by_tx.append(hashxs)
            self.touched_hashxs.update(hashxs)

        self.db.history.add_unflushed(hashxs_by_tx, tx_num_start)

    def backup_txs(self, txs, is_unspendable) -> None:
        # The base implementation removes all histories by transaction number,
        # but the synthetic namespace hashXs must also be marked as touched so
        # subscribed clients and the session history cache are invalidated.
        for tx in txs:
            for txout in tx.outputs:
                namespace_script = parse_namespace_script(txout.pk_script)
                if namespace_script is None:
                    continue
                self.touched_hashxs.add(
                    namespace_index_hashX(namespace_script.namespace)
                )
                self.touched_hashxs.add(
                    namespace_key_index_hashX(namespace_script)
                )
        super().backup_txs(txs, is_unspendable)


class WiiicoinElectrumX(ElectrumX):
    """ElectrumX session exposing Wiiicoin namespace-compatible RPC calls."""

    def set_request_handlers(self, ptuple):
        super().set_request_handlers(ptuple)

        handlers = {
            "get_transactions_info": self.phandle_namespace_get_transactions_info,
            "get_keyvalues": self.phandle_namespace_get_keyvalues,
        }
        for prefix in (
                "blockchain.wiii",
                "blockchain.wiiicoin",
                "blockchain.namespace",
        ):
            for suffix, handler in handlers.items():
                self.request_handlers[f"{prefix}.{suffix}"] = handler

    async def _read_transaction(self, txid_hum: str) -> Tx:
        assert_txid_hum(txid_hum)
        raw_tx_hex = await self.daemon_request(
            "getrawtransaction", txid_hum, False
        )
        if not isinstance(raw_tx_hex, str):
            raise RPCError(
                BAD_REQUEST,
                f"daemon returned an invalid raw transaction for {txid_hum}",
            )
        try:
            raw_tx = bytes.fromhex(raw_tx_hex)
            return self.coin.DESERIALIZER(raw_tx).read_tx()
        except (AssertionError, IndexError, TypeError, ValueError) as error:
            raise RPCError(
                BAD_REQUEST,
                f"could not decode transaction {txid_hum}: {error}",
            ) from None

    @staticmethod
    def _namespace_info(
            namespace_script: NamespaceScript,
            output_index: int,
            include_key_value: bool,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "n": [namespace_script.namespace_id, output_index],
        }
        if include_key_value:
            key_value: dict[str, Any] = {
                "op": namespace_script.operation,
                "key": base64.b64encode(namespace_script.key).decode("ascii"),
            }
            if namespace_script.value is not None:
                key_value["value"] = base64.b64encode(
                    namespace_script.value
                ).decode("ascii")
            result["kv"] = key_value
        return result

    async def phandle_namespace_get_transactions_info(
            self,
            txids: Any,
            namespace_info: Any = True,
    ) -> list[dict[str, Any]]:
        if not isinstance(txids, list):
            raise RPCError(BAD_REQUEST, "expected a list of transaction hashes")
        if len(txids) > MAX_NAMESPACE_INFO_TXS:
            raise RPCError(
                BAD_REQUEST,
                f"too many transactions, max: {MAX_NAMESPACE_INFO_TXS}",
            )
        if namespace_info not in (True, False):
            raise RPCError(BAD_REQUEST, '"namespace_info" must be a boolean')

        results: list[dict[str, Any]] = []
        for txid_hum in txids:
            assert_txid_hum(txid_hum)
            tx = await self._read_transaction(txid_hum)
            result: dict[str, Any] = {}
            for output_index, txout in enumerate(tx.outputs):
                parsed = parse_namespace_script(txout.pk_script)
                if parsed is not None:
                    result = self._namespace_info(
                        parsed,
                        output_index,
                        include_key_value=namespace_info,
                    )
                    break
            results.append(result)

        self.bump_cost(0.1 + len(results) * 0.25)
        return results

    async def phandle_namespace_get_keyvalues(
            self,
            scripthash: Any,
            start_tx_num: Any = -1,
    ) -> dict[str, Any]:
        hashx = scripthash_to_hashX(scripthash)
        try:
            start_tx_num = int(start_tx_num)
        except (TypeError, ValueError):
            raise RPCError(
                BAD_REQUEST,
                f"{start_tx_num} should be an integer transaction number",
            ) from None
        if start_tx_num < -1:
            raise RPCError(
                BAD_REQUEST,
                f"{start_tx_num} should be -1 or a non-negative transaction number",
            )

        history, cost = await self.session_mgr.limited_history(hashx)
        self.bump_cost(cost + len(history) * 0.25)

        keyvalues: list[dict[str, Any]] = []

        # The legacy API is newest-first. Wiiiwallet currently passes -1 and
        # consumes the returned key/value records directly. Positive cursors
        # remain accepted for wire compatibility; the current chain is small
        # enough to return the complete bounded ElectrumX history.
        for txid_rev, height in reversed(history):
            txid_hum = hash_to_hex_str(txid_rev)
            tx = await self._read_transaction(txid_hum)

            for txout in tx.outputs:
                parsed = parse_namespace_script(txout.pk_script)
                if parsed is None:
                    continue
                if hashx not in (
                        namespace_index_hashX(parsed.namespace),
                        namespace_key_index_hashX(parsed)):
                    continue

                item: dict[str, Any] = {
                    "tx_hash": txid_hum,
                    "height": height,
                    "type": parsed.operation_name,
                    "key": base64.b64encode(parsed.key).decode("ascii"),
                }
                if parsed.value is not None:
                    item["value"] = base64.b64encode(
                        parsed.value
                    ).decode("ascii")
                if height > 0:
                    header = await self.session_mgr.raw_header(height)
                    if len(header) >= 72:
                        item["time"] = int.from_bytes(
                            header[68:72], "little"
                        )
                keyvalues.append(item)

        return {
            "keyvalues": keyvalues,
            "min_tx_num": -1,
        }
