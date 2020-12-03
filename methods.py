from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.builder.transaction_builder import CallTransactionBuilder, TransactionBuilder, DeployTransactionBuilder
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.signed_transaction import SignedTransaction
icon_service = IconService(HTTPProvider('http://13.57.193.25:9000/', 3))

class Test(object):

    def __init__(self):
        pass

    def asset_count(self):
        call = CallBuilder().from_('hxe7af5fcfd8dfc67530a01a0e403882687528dfcb')\
            .to('cxa7ad4817078015ef25503942822442a4aa22dcec')\
            .method('asset_count')\
            .params({})\
            .build()
        return icon_service.call(call)

    def get_account_positions(self, _owner):
        call = CallBuilder().from_('hxe7af5fcfd8dfc67530a01a0e403882687528dfcb')\
            .to('cxa7ad4817078015ef25503942822442a4aa22dcec')\
            .method('get_account_positions')\
            .params({'_owner': _owner})\
            .build()
        return icon_service.call(call)

    def get_available_assets(self):
        call = CallBuilder().from_('hxe7af5fcfd8dfc67530a01a0e403882687528dfcb')\
            .to('cxa7ad4817078015ef25503942822442a4aa22dcec')\
            .method('get_available_assets')\
            .params({})\
            .build()
        return icon_service.call(call)

    def get_total_collateral(self):
        call = CallBuilder().from_('hxe7af5fcfd8dfc67530a01a0e403882687528dfcb')\
            .to('cxa7ad4817078015ef25503942822442a4aa22dcec')\
            .method('get_total_collateral')\
            .params({})\
            .build()
        return icon_service.call(call)

    def name(self):
        call = CallBuilder().from_('hxe7af5fcfd8dfc67530a01a0e403882687528dfcb')\
            .to('cxa7ad4817078015ef25503942822442a4aa22dcec')\
            .method('name')\
            .params({})\
            .build()
        return icon_service.call(call)

