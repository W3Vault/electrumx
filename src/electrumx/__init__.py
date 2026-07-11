PYTHON_MIN_VERSION = (3, 10)  # noqa: E402


from electrumx.server.controller import Controller
from electrumx.server.env import Env

# Import custom coin definitions after the core server modules have loaded.
# Coin.lookup_coin_class() discovers subclasses dynamically.
from electrumx.lib.coins_wiiicoin import Wiiicoin as _Wiiicoin  # noqa: F401,E402


BRANDING = "W3Vault"
__version__ = "2.0.0"
version = f'ElectrumX {__version__}'
version_short = __version__
