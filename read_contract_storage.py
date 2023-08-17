#!/usr/bin/env python3
###################################

import os
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address
from web3 import Web3
from utils import init_w3
import argparse
import dotenv

def read_contract_storage(contract_address: ChecksumAddress, network: str, count: int = 256, debug: bool = False):
    # Initialize web3 instance
    w3 = init_w3.setup_w3(network)

    def get_storage(ca, n):
        ret = w3.eth.get_storage_at(ca, n)
        if debug:
            print('[+] Slot: %s, Value: %s' % (n, ret))
        return ret

    # Check if the given address is valid
    if not w3.is_address(contract_address):
        print("Invalid contract address")
        return

    # Convert the address to its checksummed version
    contract_address = w3.to_checksum_address(contract_address)

    # Read the first 256 storage values
    storage_values = [get_storage(contract_address, i) for i in range(count)]
    return storage_values


# Example usage
dotenv.load_dotenv()
args = argparse.ArgumentParser()
args.add_argument('contract', type=str, help='The contract to read storage from.')
args.add_argument('-n', '--network', type=str, default='goerli',
                  help='The network to connect to. See docs.')
args.add_argument('-c', '--count', type=int, default=256, help='How many storage slots to read.')
args.add_argument('-d', '--debug', action='store_true', help='Print values as we get them.')
args = args.parse_args()

values = read_contract_storage(to_checksum_address(args.contract), args.network, args.count, args.debug)
for index, value in enumerate(values):
    print(f"Storage slot {index}: {value}")