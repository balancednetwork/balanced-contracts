from iconservice import *

class DummyOracle(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

        # All maps have the format: map[base][quote] -> value
        self._last_update_base = DictDB('last_update_base', db, value_type=int, depth=2)
        self._last_update_quote = DictDB('last_update_quote', db, value_type=int, depth=2)
        self._rate = DictDB('rate', db, value_type=int, depth=2)


    def on_install(self) -> None:
        super().on_install()
        # USD/ICX Price
        self._rate["USD"]["ICX"] = 597955725813433531
        self._last_update_base["USD"]["ICX"] = 1602202275702605
        self._last_update_quote["USD"]["ICX"] = 1602202190000000

        # DOGE/USD Price
        self._rate["DOGE"]["USD"] = 50784000000000000
        self._last_update_base["DOGE"]["USD"] = 1616643098000000
        self._last_update_quote["DOGE"]["USD"] = 1616643311790241

        # XLM/USD Price
        self._rate["XLM"]["USD"] = 360358450000000000
        self._last_update_base["XLM"]["USD"] = 1616650080000000
        self._last_update_quote["XLM"]["USD"] = 1616650390762201


    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "FakeBandOracle"

    @external(readonly=True)
    def get_reference_data(self, _base: str, _quote: str) -> dict:
        if _base == "USD" and _quote == "ICX":
            return {"rate": 597955725813433531, "last_update_base": 1602202275702605, "last_update_quote": 1602202190000000}
        if _base == "DOGE" and _quote == "USD":
            return {"rate": 50784000000000000, "last_update_base": 1616643098000000, "last_update_quote": 1616643311790241}
        if _base == "XLM" and _quote == "USD":
            return {"rate": 360358450000000000, "last_update_base": 1616650080000000, "last_update_quote": 1616650390762201}

    def is_allowed_update(self, _base: str, _quote: str) -> bool:
        allowed_update = False

        if _base == "USD" and _quote == "ICX":
            allowed_update = True
        elif _base == "DOGE" and _quote == "USD":
            allowed_update = True
        elif _base == "XLM" and _quote == "USD":
            allowed_update = True
        
        return allowed_update

    @external
    def rig_the_market(self, _base: str, _quote: str, _rate: int) -> None:
        update_time = self.now()

        if not self.is_allowed_update(_base, _quote):
            revert("Cannot update the price of this pair")
        
        if _rate < 0:
            revert("rate must be positive")
        
        self._rate[_base][_quote] = _rate
        self._last_update_base[_base][_quote] = update_time
        self._last_update_quote[_base][_quote] = update_time

    def fallback(self):
        pass
