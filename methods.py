from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.builder.transaction_builder import CallTransactionBuilder, TransactionBuilder, DeployTransactionBuilder
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.signed_transaction import SignedTransaction
icon_service = IconService(HTTPProvider('http://52.53.175.151:9000/', 3))

class Test(object):

    def __init__(self):
        pass

    def asset_count(self):
        call = CallBuilder().from_('hxe7af5fcfd8dfc67530a01a0e403882687528dfcb')\
            .to('cx064b8c7b72a6b8c0987a06f9f2e1b322e6c464e8')\
            .method('asset_count')\
            .params({})\
            .build()
        return icon_service.call(call)

    def get_account_positions(self, _owner):
        call = CallBuilder().from_('hxe7af5fcfd8dfc67530a01a0e403882687528dfcb')\
            .to('cx064b8c7b72a6b8c0987a06f9f2e1b322e6c464e8')\
            .method('get_account_positions')\
            .params({'_owner': _owner})\
            .build()
        return icon_service.call(call)

    def get_available_assets(self):
        call = CallBuilder().from_('hxe7af5fcfd8dfc67530a01a0e403882687528dfcb')\
            .to('cx064b8c7b72a6b8c0987a06f9f2e1b322e6c464e8')\
            .method('get_available_assets')\
            .params({})\
            .build()
        return icon_service.call(call)

    def get_total_collateral(self):
        call = CallBuilder().from_('hxe7af5fcfd8dfc67530a01a0e403882687528dfcb')\
            .to('cx064b8c7b72a6b8c0987a06f9f2e1b322e6c464e8')\
            .method('get_total_collateral')\
            .params({})\
            .build()
        return icon_service.call(call)

    def name(self):
        call = CallBuilder().from_('hxe7af5fcfd8dfc67530a01a0e403882687528dfcb')\
            .to('cx064b8c7b72a6b8c0987a06f9f2e1b322e6c464e8')\
            .method('name')\
            .params({})\
            .build()
        return icon_service.call(call)

