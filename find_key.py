#!/usr/bin/env python3.10

import json
import math

import web3
import argparse
from binascii import Error
import os

from eth_account.signers.local import LocalAccount
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address
import concurrent.futures

from tqdm import tqdm


class Acct:
    def __init__(self, key: str, address: ChecksumAddress):
        self.key = key
        self.address = address


class KeyFinder:
    def __init__(self, output_file: str):
        self.output_file = output_file
        self.found_keys = []
        # self.addresses = addresses

    def log_result(self, acct: LocalAccount):
        if args.output:
            with open(self.output_file, 'a') as f:
                obj = {"address": acct.address, "key": str(acct.key.hex())}
                f.write(json.dumps(obj))

    def divide_chunks(self, l: list, n: int) -> list:
        def div(l, n):
            for i in range(0, len(l), n):
                yield l[i:i + n]

        gen = div(l, n)
        return [x for x in gen]

    def search(self, key):
        try:
            acct = from_key(key)
        except (Error, ValueError):
            pass

        else:
            # print(acct.address)
            # with open(args.output, 'w') as f:
            #    f.write(acct.address+'\n')
            if addresses.__contains__(to_checksum_address(acct.address)):
                self.found_keys.append((acct.address, acct.key))
                print('Found key: ', key)
                self.log_result(acct)

    def search_batch(self, batch: list):
        [self.search(key) for key in batch]


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('-f', '--input', type=str, required=True)
    args.add_argument('-o', '--output', type=str, required=False, default=False)
    args.add_argument('-a', '--addresses', type=str, required=False, default=None)
    args.add_argument('-A', '--address', type=str, default=None)
    args.add_argument('-t', '--threads', type=int, default=os.cpu_count())
    args = args.parse_args()
    keys = []
    addresses = []
    result = []
    with open(args.input, 'r') as f:
        f = f.readlines()
        for line in f:
            line = line.strip('\r\n')
            if line is not None:
                keys.append(line)
    if args.address:
        addresses.append(to_checksum_address(args.address))
    if args.addresses:
        with open(args.addresses, 'r') as f:
            f = f.readlines()
            for line in f:
                line = line.strip('\r\n')
                if line:
                    addresses.append(to_checksum_address(line))

    from_key = web3.Account.from_key
    kf = KeyFinder(args.output)
    # map(search, keys)
    batch_size = int(len(keys) / int(math.ceil(args.threads)) + 1)
    batches = kf.divide_chunks(keys, batch_size)
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=args.threads)
    for x, batch in enumerate(tqdm(batches)):
        print(f'starting batch {x + 1}/{len(batches)}')
        executor.submit(kf.search_batch, batch)
