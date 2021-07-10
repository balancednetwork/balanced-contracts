from iconservice import *


class DummyOracle(IconScoreBase):
    _RATE = 'rate'
    _LAST_UPDATE_BASE = 'last_update_base'
    _LAST_UPDATE_QUOTE = 'last_update_quote'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._rate = VarDB(self._RATE, db, value_type=int)
        self._last_update_base = VarDB(self._LAST_UPDATE_BASE, db, value_type=int)
        self._last_update_quote = VarDB(self._LAST_UPDATE_QUOTE, db, value_type=int)

    def on_install(self) -> None:
        super().on_install()
        self._rate.set(597955725813433531)
        self._last_update_base.set(1602202275702605),
        self._last_update_quote.set(1602202190000000)

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "FakeBandOracle"

    @external()
    def set_reference_data(self, _base: str, _quote: str, rate: int, last_update_base: int, last_update_quote: int) -> None:
        if _base == "USD" and _quote == "ICX":
            self._rate.set(rate)
            self._last_update_base.set(last_update_base),
            self._last_update_quote.set(last_update_quote)
        # if _base == "DOGE" and _quote == "USD":
        #     self._rate.set(rate)
        #     self._last_update_base.set(last_update_base),
        #     self._last_update_quote.set(last_update_quote)
        # if _base == "XLM" and _quote == "USD":
        #     self._rate.set(rate)
        #     self._last_update_base.set(last_update_base),
        #     self._last_update_quote.set(last_update_quote)

    @external(readonly=True)
    def get_reference_data(self, _base: str, _quote: str) -> dict:
        if _base == "USD" and _quote == "ICX":
            return {"rate": self._rate.get(), "last_update_base": self._last_update_base.get(),
                    "last_update_quote": self._last_update_quote.get()}
            # return {"rate": 597955725813433531, "last_update_base": 1602202275702605, "last_update_quote": 1602202190000000}
        # if _base == "DOGE" and _quote == "USD":
        #     return {"rate": self._rate.get(), "last_update_base": self._last_update_base.get(),
        #             "last_update_quote": self._last_update_quote.get()}
        #     # return {"rate": 50784000000000000, "last_update_base": 1616643098000000, "last_update_quote": 1616643311790241}
        # if _base == "XLM" and _quote == "USD":
        #     return {"rate": self._rate.get(), "last_update_base": self._last_update_base.get(),
        #             "last_update_quote": self._last_update_quote.get()}
        #     # return {"rate": 360358450000000000, "last_update_base": 1616650080000000, "last_update_quote": 1616650390762201}

    def fallback(self):
        pass
