# Wiiicoin configuration

This fork includes a Wiiicoin main-network definition.

## Install

Install ElectrumX with a database backend and the Wiiicoin hashing extra:

```bash
python -m pip install -e '.[leveldb,wiiicoin]'
```

If the system already has a compatible `pycryptonight` module installed, the
`wiiicoin` extra may be omitted.

## Environment

Set the normal ElectrumX variables and select Wiiicoin with:

```bash
export COIN=Wiiicoin
export NET=main
export DAEMON_URL=http://rpcuser:rpcpassword@127.0.0.1:8688/
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

The configured network values are:

- Coin name: `Wiiicoin`
- Network: `main`
- Symbol: `WIII`
- Daemon RPC port: `8688`
- Electrum TCP port: `50001`
- Electrum SSL port: `50002`
- P2PKH prefix: `0x87`
- P2SH prefix: `0x7d`
- Header size: `157` bytes
- Genesis hash: `000000b6342a3f29e384a67490086d5dd987f6947a4308d56a893294b96fa146`
