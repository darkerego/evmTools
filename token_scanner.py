#!/usr/bin/env python3
import argparse
import binascii
import os

import aiofiles
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address
from web3 import HTTPProvider, Web3
from web3.middleware import geth_poa_middleware

from utils import ahttp
import asyncio
import json
import tqdm.asyncio as tqdm
import libs.abi_lib
import web3
import dotenv


class Acct:
    def __init__(self, key: (str, bytes, None), address: (str, None, ChecksumAddress)):
        self.key = key
        self.address = address


class TokenData:
    contract_address: ChecksumAddress = None
    holder_acct: Acct = None
    symbol: str = None
    name: str = None
    decimals: int = 0
    balance: int = 0

    def as_dict(self):
        return {'contract_address': self.contract_address, 'address': self.holder_acct.address,
                'key': self.holder_acct.key.hex(), 'symbol': self.symbol, 'name': self.name,
                'decimals': self.decimals, 'balance': self.balance}


class HecoScanner:
    def __init__(self, output_file: str, network: str = 'heco', delay: float = 0.2):
        dotenv.load_dotenv()
        self.delay = delay
        self.bscan_api_key = os.environ.get('bscan_api_key')
        self.network = network
        self.output_file = output_file
        self.http = None
        self.w3: Web3 = Web3(HTTPProvider(os.environ.get(f'{network}_http_endpoint')))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.report_dict = {}

    async def __ainit__(self):
        headers = {'content-type': 'application/json'}
        self.http = ahttp.AsyncHttpClient(_headers=headers)
        await self.http.__ainit__()

    async def get_token_tx_address(self, address: ChecksumAddress):
        if self.network == 'heco':
            url = f"""https://api.hecoinfo.com/api?module=account&action=tokentx&address={address}&startblock=0&endblock=999999999&sort=asc"""
        elif self.network == 'bsc':
            url = f"""https://api.bscscan.com/api?module=account&action=tokentx&address={address}&&startblock=0&endblock=999999999&sort=asc&apikey={self.bscan_api_key}"""
        else:
            print('[!] I only wrote functionality for heco and bsc, so you have to modify me to work on %s' % self.network)
            exit(1)
        return await self.http.request('get', path=url)

    async def parse_token_addresses(self, acct: Acct, c=1):

        tokens: list[TokenData] = []
        status, ret = await self.get_token_tx_address(acct.address)
        await asyncio.sleep(float(self.delay))
        if status == 0:
            if c > 4:
                print('[!] Not-so-transient connection error... exiting')
                exit(1)
            await asyncio.sleep(2 * c)
            return await self.parse_token_addresses(acct, c+1)
        if status == 200:
            data = ret.get('result')
            # print(data)
            for tx in data:
                # print(tx)
                token_data = TokenData()
                token_data.holder_acct = acct
                token_data.contract_address = to_checksum_address(tx.get('contractAddress'))
                token_data.name = tx.get('tokenName')
                token_data.symbol = tx.get('tokenSymbol')
                token_data.decimals = tx.get('tokenDecimal')
                tokens.append(token_data)
        return tokens

    def token_contract_obj(self, contract_address: ChecksumAddress):
        return self.w3.eth.contract(contract_address, abi=libs.abi_lib.EIP20_ABI)

    async def token_balance(self, contract_address: ChecksumAddress, holder_address: ChecksumAddress) -> int:
        contract = self.token_contract_obj(contract_address)
        return contract.functions.balanceOf(holder_address).call()

    async def log_balance(self, data: TokenData):
        if self.report_dict.get(data.holder_acct.address):
            self.report_dict[data.holder_acct.address].append(data.as_dict())
        else:
            self.report_dict[data.holder_acct.address] = [data.as_dict()]

        async with aiofiles.open(self.output_file, 'w') as f:
            await f.write(json.dumps(self.report_dict))

    async def get_token_balances(self, acct: Acct):
        if acct is None:
            return
        token_data_lst = await self.parse_token_addresses(acct)
        processed_tokens = []
        for data in token_data_lst:
            if not processed_tokens.__contains__(data.contract_address) and data is not None:

                balance = await self.token_balance(data.contract_address, data.holder_acct.address)
                if balance > 0:
                    data.balance = balance
                    print(data.as_dict())
                processed_tokens.append(data.contract_address)
                await self.log_balance(data)

    def parse_key(self, key: str):
        try:
            account = web3.Account.from_key(key)
        except (ValueError, binascii.Error):
            try:
                to_checksum_address(key)
            except (ValueError, binascii.Error):
                return None
            else:
                return Acct(None, key)
        else:
            return account


async def main(file: str, output_file: str, seek: int, network: str, delay: float):
    hs = HecoScanner(output_file, network, delay)
    with open(file) as f:
        keys = list(sorted(set([line.strip('\r\n') for line in f.readlines()])))
    accounts = []
    for key in keys:
        accounts.append(hs.parse_key(key))

    await hs.__ainit__()
    progress = tqdm.tqdm(accounts, f'{network} scanner')
    if len(accounts):
        for x, acct in enumerate(progress.iterable):
            if x >= seek:
                await hs.get_token_balances(acct)
            progress.update()


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('file', type=str)
    args.add_argument('-o', '--output', default=None, help='Log json output to file.')
    args.add_argument('-s', '--seek', type=int, default=0, help='Seek to.')
    args.add_argument('-n', '--network', type=str, default='heco', choices=['heco', 'bsc'])
    args.add_argument('-d', '--delay', type=float, default=0.2, help='Request throttling sleep interval. '
                                                                     'In some cases, you may want '
                                                                     'to adjust this.')
    args = args.parse_args()
    asyncio.run(main(args.file, args.output, args.seek, args.network, args.delay))
