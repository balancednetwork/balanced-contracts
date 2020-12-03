from iconservice import *

@eventlog(indexed=3)
def Transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
    pass

@eventlog(indexed=2)
def FundTransfer(self, destination: Address, amount: int, note: str):
    pass

@eventlog(indexed=2)
def TokenTransfer(self, recipient: Address, amount: int, note: str):
    pass

@eventlog(indexed=3)
def OriginateLoan(self, recipient: Address, symbol: str, amount: int, note: str):
    pass

@eventlog(indexed=3)
def LoanRepaid(self, account: Address, symbol: str, amount: int, note: str):
    pass

@eventlog(indexed=3)
def AssetRedeemed(self, account: Address, symbol: str, amount: int, note: str):
    pass

@eventlog(indexed=2)
def Liquidate(self, account: Address, amount: int, note: str):
    pass

@eventlog(indexed=3)
def BadDebt(self, account: Address, symbol: str, amount: int, note: str):
    pass

@eventlog(indexed=2)
def TotalDebt(self, symbol: str, amount: int, note: str):
    pass

@eventlog(indexed=3)
def FeePaid(self, symbol: str, amount: int, type: str, note: str):
    pass

@eventlog(indexed=2)
def OraclePriceUpdate(self, symbol: str, rate: int, note: str):
    pass
