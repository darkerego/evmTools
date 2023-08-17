#!/usr/bin/env python3

"""
Program that takes raw transaction data from an EVM smart contract call and attempts to figure out
the parameters, and their possible data types. Useful if you are trying to reverse engineer a smart
contract that you do not have the source code for.

Example usage. This is an approve(address, uint256) call:

python3 raw_tx_decode.py 0x095ea7b30000000000000000000000003a6d8ca21d1cf76f653a67577fa0d27453350dd8ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
[+] Selector: 0x095ea7b3
[+] Parameters:
[+] Parameter 0 possible data types:
('bytes', '0000000000000000000000003a6d8ca21d1cf76f653a67577fa0d27453350dd8')
('string', '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00:m\x1d\x1coe:gW\x7ftS5\r')
('uint256', 333564496818894432725139614857668300319560633816)
('int256', 333564496818894432725139614857668300319560633816)
('ethereum_address', '0x3a6d8ca21d1cf76f653a67577fa0d27453350dd8')
[+] Parameter 1 possible data types:
('bytes', 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff')
('string', '')
('uint256', 115792089237316195423570985008687907853269984665640564039457584007913129639935)
('int256', -1)
('ethereum_address', '0xffffffffffffffffffffffffffffffffffffffff')

In this example case, obviously we already know that the data types are address and uint256. It's just
for demonstration.

"""

import argparse
import binascii

import web3
from web3.exceptions import InvalidAddress


def is_ethereum_address(address):
    # print('Testing', address)
    try:
        web3.Web3.to_checksum_address(address)
        return True
    except (InvalidAddress, ValueError, binascii.Error):
        return False


def hex_to_possible_types(hex_string):
    try:
        decoded_hex = binascii.unhexlify(hex_string)
    except binascii.Error:
        return []

    int_value = int(hex_string, 16)
    uint256_value = int_value
    # Interpret large values (> 2^255) as negative numbers (two's complement)
    int256_value = int_value if int_value < 2 ** 255 else int_value - 2 ** 256

    possible_types = [
        ("bytes", decoded_hex.hex()),
        ("string", decoded_hex.decode(errors='ignore')),
        ("uint256", uint256_value),
        ("int256", int256_value),
    ]

    # Check if the last 40 characters (20 bytes) could be an address
    possible_address = '0x' + hex_string[-40:]
    if is_ethereum_address(possible_address):
        possible_types.append(("ethereum_address", possible_address))

    return possible_types


def check_for_signature(data_list_types):
    last_v, last_r, last_s = data_list_types[-3:]
    if len(last_v) > 0 and len(last_r) > 0 and len(last_s) > 0:
        signature = (last_v, last_r, last_s)
        # Remove the signature from the data_list_types
        data_list_types = data_list_types[:-3]
    else:
        signature = None
    return signature


def decode_transaction_data(data):
    function_signature = data[:10]
    inputs = data[10:]

    data_list = [inputs[n:n + 64] for n in range(0, len(inputs), 64)]

    data_list_types = [hex_to_possible_types(data) for data in data_list]

    # Check the last three items for signature
    try:
        signature = check_for_signature(data_list_types)
    except ValueError:
        signature = None

    return function_signature, data_list_types, signature


def get_substrings(input_string, n):
    # Check if n is greater than the length of the input string
    if n > len(input_string):
        return "Length n is greater than the length of the input string"

    # List to store substrings
    substrings = [input_string[i: i + n] for i in range(0, int((len(input_string) - n + 1) /n))]
    return substrings


if __name__ == "__main__":

    args = argparse.ArgumentParser()
    args.add_argument('data', type=str)
    args = args.parse_args()
    s, l, sig = decode_transaction_data(args.data)
    print('[+] Selector:', s)
    print('[+] Parameters: ')
    for x, param in enumerate(l):
        print(f'[+] Parameter {x} possible data types: ')
        for possible_data_type in param:
            print(possible_data_type)
    if sig:
        if len(sig):
            final_signature_string = ''
            for x in sig:
                for _type in x:
                    if _type[0] == 'bytes':
                        final_signature_string += _type[1]
            print('[+] Possible Signature', final_signature_string)
    print('[+] Parts', get_substrings(args.data, 64))


