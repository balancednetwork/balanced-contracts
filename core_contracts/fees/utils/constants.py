from iconservice import *

# ================== MAIN NET on_install =====================

# Main net token addresses. Can be removed after on_install is run.
IUSDC = Address.from_string("cxae3034235540b924dfcc1b45836c293dcc82bfb7")
OMM = Address.from_string("cx1a29259a59f463a67bb2ef84398b30ca56b5830a")
USDS = Address.from_string("cxbb2871f468a3008f80b08fdde5b8b951583acf06")
CFT = Address.from_string("cx2e6d0fc0eca04965d06038c8406093337f085fcf")
SICX = Address.from_string("cx2609b924e33ef00b648a409245c7ea394c467824")
BNUSD = Address.from_string("cx88fd7df7ddff82f7cc735c871dc519838cb235bb")
BALN = Address.from_string("cxf61cd5a45dc9f91c15aa65831a30a90d59a09619")

# Initial main net accepted dividend tokens. Can be removed after on_install is run.
ACCEPTED_DIVIDEND_TOKENS_MAIN_NET = [
    BALN,
    BNUSD,
    SICX
]

# Initial main net routes. Can be removed after on_install is run.
INITIAL_ROUTES_MAIN_NET = [
    [IUSDC, BALN, [BNUSD, BALN]],
    [OMM, BALN, [SICX, BALN]],
    [USDS, BALN, [BNUSD, BALN]],
    [CFT, BALN, [SICX, BALN]]
]