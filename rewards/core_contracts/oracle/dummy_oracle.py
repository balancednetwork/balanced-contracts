from iconservice import *

class DummyOracle(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self) -> None:
        super().on_install()

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


    def fallback(self):
        pass
