#!/usr/bin/env python3
import argparse
import os
import time

import dotenv
import tqdm
import web3
from eth_account.signers.local import LocalAccount
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address
from hexbytes import HexBytes
from web3.contract import Contract
from web3.exceptions import ContractLogicError
from web3.middleware import geth_poa_middleware
from libs.style import PrettyText
import libs.abi_lib
import requests
from utils.helpers import load_json, dump_json
from utils.constants import Constants

zero_address = Constants.zero_address


class Token:
    def __init__(self, address: (str, ChecksumAddress), decimals: int):
        self.address: ChecksumAddress = web3.Web3.to_checksum_address(address)
        self.decimals: int = decimals


class PancakeSwapDeployments:
    router_address: ChecksumAddress = web3.Web3.to_checksum_address("0x10ED43C718714eb63d5aA57B78B54704E256024E")
    factory_address: ChecksumAddress = web3.Web3.to_checksum_address("0xca143ce32fe78f1f7019d7d551a6402fc5350c73")
    bsc_usdt: Token = Token("0x55d398326f99059fF775485246999027B3197955", 18)
    bsc_usdc: Token = Token("0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d", 18)
    bsc_dai: Token = Token("0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3", 18)
    wrapped_native: Token = Token("0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c", 18)

    def __init__(self, _w3: web3.Web3):
        self.w3 = _w3
        self.factory_obj = self.contract_object(self.factory_address, libs.abi_lib.mdex_factory)
        self.router_obj = self.contract_object(self.router_address, libs.abi_lib.mdex_router)

    def contract_object(self, address: ChecksumAddress, abi: dict):
        return self.w3.eth.contract(address, abi=abi)

    def mdex_pair(self, pair_address: ChecksumAddress) -> Contract:
        return self.w3.eth.contract(pair_address, abi=libs.abi_lib.mdex_pair)


class MdexDeployments:
    router_address: ChecksumAddress = web3.Web3.to_checksum_address('0x0f1c2d1fdd202768a4bda7a38eb0377bd58d278e')
    factory_address: ChecksumAddress = web3.Web3.to_checksum_address('0xb0b670fc1f7724119963018db0bfa86adb22d941')

    heco_usdt: Token = Token("0xa71edc38d189767582c38a3145b5873052c3e47a", 18)
    heco_husd: Token = Token("0x0298c2b32eae4da002a15f36fdf7615bea3da047", 8)
    wrapped_native: Token = Token("0x5545153ccfca01fbd7dd11c0b23ba694d9509a6f", 18)
    heco_usdc: Token = Token("0x9362bbef4b8313a8aa9f0c9808b80577aa26b73b", 6)

    def __init__(self, _w3: web3.Web3):
        self.w3 = _w3
        self.factory_obj = self.contract_object(self.factory_address, libs.abi_lib.mdex_factory)
        self.router_obj = self.contract_object(self.router_address, libs.abi_lib.mdex_router)

    def contract_object(self, address: ChecksumAddress, abi: dict):
        return self.w3.eth.contract(address, abi=abi)

    def mdex_pair(self, pair_address: ChecksumAddress) -> Contract:
        return self.w3.eth.contract(pair_address, abi=libs.abi_lib.mdex_pair)


def setup_w3(network: str) -> (web3.Web3, False):
    dotenv.load_dotenv()
    endpoint = os.environ.get(f'{network}_http_endpoint')
    w3 = web3.Web3(web3.HTTPProvider(endpoint))
    if w3.is_connected():
        print(f'[+] Web3 connected to {w3.eth.chain_id}')
        if w3.eth.chain_id in [56, 128, 137]:
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return w3
    return False


class MdexClient:
    def __init__(self, network: str, account: (LocalAccount, str, HexBytes, None) = None, verbosity: int = 0):
        self.print = PrettyText(verbosity)
        self.last_conn_check: int = 0
        self.network: str = network

        self._w3: web3.Web3 = setup_w3(network)
        self.account: LocalAccount = self.setup_account(account)
        if self.network == 'heco':
            print('[+] Loading Mdex deployments')
            self.deployments = MdexDeployments(self._w3)
            self.router: Contract = self.deployments.router_obj
            self.factory: Contract = self.deployments.factory_obj
            self.quote_tokens = [self.deployments.wrapped_native,
                                 self.deployments.heco_usdt,
                                 self.deployments.heco_husd,
                                 self.deployments.heco_usdc]
            self.native_price = self.get_ht_price()
        else:
            print('[+] Loading pancake deployments')
            self.deployments = PancakeSwapDeployments(self._w3)
            self.router: Contract = self.deployments.router_obj
            self.factory: Contract = self.deployments.factory_obj
            self.quote_tokens = [self.deployments.wrapped_native,
                                 self.deployments.bsc_usdt,
                                 self.deployments.bsc_usdc,
                                 self.deployments.bsc_dai]
            self.native_price = self.get_ht_price()

    @property
    def w3(self):
        if not self.last_conn_check or self.last_conn_check - time.time() >= 60:
            if self._w3.is_connected():
                pass
            else:
                self.print.error('W3 Disconnected! Reconnecting ... ')
                self._w3 = setup_w3(self.network)
        return self._w3

    def get_ht_price(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.hecoinfo.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-User': '?1',
        }

        params = {
            'module': 'stats',
            'action': 'price',
        }
        if self.network == 'heco':
            response = requests.get('https://api.hecoinfo.com/api', params=params, headers=headers)
        else:
            response = requests.get(
                f"https://api.bscscan.com/api?module=stats&action=bnbprice&apikey={os.environ.get('bscan_api_key')}")
        if response.status_code == 200:
            print(response.json())
            if self.network == 'heco':
                price = response.json().get('result').get('coinusd')
            else:
                price = response.json().get('result').get('ethusd')

            return float(price)
        else:
            err = response.text
            self.print.error(f'Error fetching HT price from api: {err}')
            return 0.0

    def setup_account(self, account: (LocalAccount, str, HexBytes, None)):
        """
        Set up default account for signing transactions and swapping, etc.
        :param account: Either a LocalAccount object, private key, path to a json
        wallet file, or None Type -- in the last case, we load from `keys/default_wallet.json`
        :return:
        """

        def json_load_account(acct: any) -> (LocalAccount, None):
            if os.path.exists(acct):
                return self.w3.eth.account.from_key(load_json(account).get('wallet').get('private_key'))
            return False

        if type(account) is LocalAccount:
            return account
        if type(account) in [str, HexBytes]:
            if len(account) >= 64 <= 66:
                return web3.Account.from_key(account)
            else:
                return json_load_account(account)
        if type(account) is None:
            return json_load_account('keys/default_wallet.json')

    def _quote(self, amount: int, token_address: ChecksumAddress, quote_token: Token):
        # print(f'[~] Getting quote {amount} {token_address} {quote_token.address} ')
        # print(self.router.address)
        assert to_checksum_address(token_address) != to_checksum_address(quote_token.address)
        try:
            ret = self.router.functions.getAmountsOut(amount, [token_address, quote_token.address]).call()
        except ContractLogicError as err:
            # print(err)
            return 0
        else:
            quote_raw_in, quote_raw_out = ret[0], ret[1]
            quote_out = quote_raw_out / (10 ** quote_token.decimals)
            if quote_token.address == self.deployments.wrapped_native.address:
                return quote_out * self.native_price
            return quote_out

    def quote(self, token_address: ChecksumAddress, amount: int):
        """
        uint256: { "0": "451589303671210092782648", "1": "170612273489226474404698", "reserveA": "451589303671210092782648", "reserveB": "170612273489226474404698" }
        :param amount: raw token balance
        :param token_address:
        :return:
        """

        # pair_address = None
        # token_address
        token_address = to_checksum_address(token_address)
        """if token_address == self.mdex_deployments.heco_usdt.address:
            quote_token = self.mdex_deployments.wrapped_heco
        else:
            quote_token = self.mdex_deployments.heco_usdt"""
        for x, token in enumerate(self.quote_tokens):
            if token_address == token.address:
                try:
                    _token = self.quote_tokens[x + 1]
                except IndexError:
                    _token = self.quote_tokens[x - 1]

                _quote_ = self._quote(amount, token_address, _token)
                #print(f'Checking {token_address} try: {x}, quote: {_quote_}')
            else:
                _quote_ = self._quote(amount, token_address, token)
                # print(f'Checking {token_address} try: {x}')
                if _quote_ > 0:
                    return _quote_
        return 0


def quote(mdex: MdexClient, token, amount):
    return mdex.quote(web3.Web3.to_checksum_address(token), int(amount))


def main(file: str, output_file: str = None, threshold: float = 0, verbosity: int = 0, network: str = 'heco'):
    mdex = MdexClient(network, 'keys/anon_31.json', verbosity)
    token_dict = load_json(file)

    for acct, data_list in tqdm.tqdm(token_dict.items()):
        for x, data in enumerate(data_list):
            token_address = data.get('contract_address')
            balance = mdex.deployments.contract_object(token_address, libs.abi_lib.EIP20_ABI).functions.balanceOf(
                acct).call()
            # print(balance)
            if balance > 0:
                _quote = quote(mdex, token_address, balance)
                if _quote > 0 and _quote > threshold:
                    token_dict[acct][x].update({'quote': _quote})
                    dump_json(output_file, token_dict)
                    print(token_dict[acct][x])


if __name__ == '__main__':
    dotenv.load_dotenv()
    args = argparse.ArgumentParser()
    args.add_argument('-n', '--network')
    subparsers = args.add_subparsers(dest='command')

    single_quote = subparsers.add_parser('single')
    single_quote.add_argument('token', type=str, help='Token address to quote')
    single_quote.add_argument('amount', type=int, help='Raw integer amount.')

    list_quote = subparsers.add_parser('list')
    list_quote.add_argument('-f', '--file', type=str)
    list_quote.add_argument('-o', '--output', type=str, default=None)
    list_quote.add_argument('-t', '--threshold', type=float, default=0)
    args.add_argument('-v', '--verbosity', action='count', default=0)

    args = args.parse_args()
    main(args.file, args.output, args.threshold, args.verbosity, args.network)
