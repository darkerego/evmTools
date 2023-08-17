#!/usr/bin/env python3
import asyncio
import binascii
import sys

import web3
import os
import dotenv
from eth_account.signers.local import LocalAccount

dotenv.load_dotenv()
endpoint = os.environ.get('ethereum_ws_endpoint')
w3 = web3.Web3(web3.WebsocketProvider(endpoint))


def parse_keys(file: str) -> list[LocalAccount]:
    print('[!] Opening %s' % file)
    accounts: list[LocalAccount] = []
    with open(file, 'r') as f:
        f = f.readlines()
        for line in f:
            try:
                acct = web3.Account.from_key(line.strip('\r\n'))
            except (ValueError, binascii.Error):
                pass
            else:
                accounts.append(acct)
    return accounts


async def _check_nonce(acct: LocalAccount) -> int:
    return w3.eth.get_transaction_count(acct.address)


async def check_nonce(acct: LocalAccount):
    return {'address': acct.address, 'key': acct.key.hex(), 'nonce': await _check_nonce(acct)}


def divide_chunks(l: list, n: int) -> list:
    def split_gen(ll: list, nn: int):
        for i in range(0, len(ll), nn):
            yield ll[i:i + nn]

    """
    Split a list
    :param l: list
    :param n: batch size
    :return: generator
    """
    # unwrap the generator
    return [chunk for chunk in split_gen(l, n)]


async def main(file: str):
    eth_accounts = parse_keys(file)
    print(f'[+] Found {len(eth_accounts)}')
    batches = divide_chunks(eth_accounts, 10)
    for batch in batches:
        tasks = []
        for acct in batch:
            tasks.append(asyncio.create_task(check_nonce(acct)))
        results = await asyncio.gather(*tasks)
        for res in results:
            if res.get('nonce') > 0:
                print(res)


if __name__ == '__main__':
    if not len(sys.argv):
        print('usage: %s input_file' % sys.argv[0])
        exit()
    file = sys.argv[1]
    asyncio.run(main(file))
