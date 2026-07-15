# Wiiicoin configuration

This fork includes a Wiiicoin main-network definition.

## Install

Install ElectrumX with a database backend and the Wiiicoin hashing extra:

```bash
python -m pip install -e '.[leveldb,wiiicoin]'
```

The `wiiicoin` extra installs `pycryptodomex`, which provides the Keccak-256
header hashing used by this chain.

## Environment

Set the normal ElectrumX variables and select Wiiicoin with:

```bash
export COIN=Wiiicoin
export NET=main
export DAEMON_URL=http://rpcuser:rpcpassword@127.0.0.1:8868/
export DB_DIRECTORY=/var/lib/electrumx/wiiicoin
export SERVICES=tcp://0.0.0.0:50001,ssl://0.0.0.0:50002
export SSL_CERTFILE=/etc/electrumx/server.crt
export SSL_KEYFILE=/etc/electrumx/server.key
```

The Wiiicoin daemon must have RPC enabled and be fully synchronized before
starting ElectrumX.

## Start

```bash
electrumx_server
```

## Namespace support

The Wiiicoin session exposes the namespace calls used by Wiiiwallet:

- `blockchain.keva.get_transactions_info`
- `blockchain.keva.get_keyvalues`
- `blockchain.wiiicoin.get_transactions_info`
- `blockchain.wiiicoin.get_keyvalues`
- `blockchain.namespace.get_transactions_info`
- `blockchain.namespace.get_keyvalues`

Namespace control outputs are indexed against the trailing owner-address
script, while additional synthetic indexes provide generic namespace history
and namespace/key history.

These indexes change the Wiiicoin database layout. After upgrading an existing
server, stop ElectrumX, remove or rename the existing `DB_DIRECTORY`, and allow
the server to resynchronize from block zero before reconnecting Wiiiwallet.

A direct TCP capability check can be made with:

```bash
printf '%s\n' \
  '{"id":1,"method":"server.version","params":["namespace-test","1.4"]}' \
  '{"id":2,"method":"blockchain.keva.get_transactions_info","params":[[],true]}' \
  | nc -w 5 127.0.0.1 50001
```

The second response should contain an empty result array rather than a
`method not found` error.

The configured network values are:

- Coin name: `Wiiicoin`
- Network: `main`
- Symbol: `WIII`
- Daemon RPC port: `8868`
- Electrum TCP port: `50001`
- Electrum SSL port: `50002`
- P2PKH prefix: `0x87`
- P2SH prefix: `0x7d`
- Header size: variable, encoded from byte 80 of each block
- Genesis hash: `000000b6342a3f29e384a67490086d5dd987f6947a4308d56a893294b96fa146`
