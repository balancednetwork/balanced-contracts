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
        return {"rate": 597955725813433531, "last_update_base": 1602202275702605, "last_update_quote": 1602202190000000}

    def fallback(self):
        pass
