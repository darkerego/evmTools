#!/usr/bin/env python3
###########################################
# Darkerego, 2023
###########################################
import web3
from eth_typing import ChecksumAddress
from web3 import Web3
from rlp import encode
import argparse
from utils import init_w3


def compute_contract_address(sender_address: str, nonce: int) -> str:
    """
    Compute the address of a contract created by a transaction from sender_address with nonce.
    """
    # Ensure inputs are in the right format
    sender_address_bytes = Web3.to_bytes(hexstr=web3.Web3.to_checksum_address(sender_address))
    nonce_bytes = Web3.to_bytes(nonce)

    # RLP encode the structure containing the sender's address and the sender's nonce
    rlp_encoded = encode([sender_address_bytes, nonce_bytes])

    # Take the Keccak-256 hash
    hashed = Web3.keccak(rlp_encoded)

    # The contract address is the last 20 bytes of this hash
    contract_address = Web3.to_hex(hashed[-20:])

    return contract_address


def get_current_nonce(_w3: web3.Web3, addr: ChecksumAddress) -> int:
    return _w3.eth.get_transaction_count(addr)

def compute_contract_address_nonce(network: str, addr: ChecksumAddress, nonce_increment: int = 0):
    w3 = init_w3.setup_w3(network)
    nonce = get_current_nonce(w3, addr) + nonce_increment
    ret = compute_contract_address(addr, nonce)
    print(f'[+] Contract for account {addr} at nonce {nonce} is : {ret}')


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('address', type=str, default=None)
    args.add_argument('-i', '--increment', type=int, default=0)
    args.add_argument('-n', '--network', type=str, default='goerli')
    args = args.parse_args()
    compute_contract_address_nonce(args.network, web3.Web3.to_checksum_address(args.address), args.increment)
