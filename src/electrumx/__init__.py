PYTHON_MIN_VERSION = (3, 10)  # noqa: E402


from electrumx.server.controller import Controller
from electrumx.server.env import Env

# Import and register custom coin definitions after the core server modules
# have loaded. Coin.lookup_coin_class() inspects names in electrumx.lib.coins,
# so expose Wiiicoin in that module's namespace as well.
from electrumx.lib import coins as _coins  # noqa: E402
from electrumx.lib.coins_wiiicoin import Wiiicoin as _Wiiicoin  # noqa: E402

_coins.Wiiicoin = _Wiiicoin


BRANDING = "W3Vault"
__version__ = "2.0.0"
version = f'ElectrumX {__version__}'
version_short = __version__
