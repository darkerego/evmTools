import binascii
import json
import os
import time

from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address


class Acct:
    def __init__(self, key: (str, bytes, None), address: (str, None, ChecksumAddress)):
        self.key = key
        self.address = address


def parse_key(key: str) -> (LocalAccount, Acct, None):
    try:
        account = Account.from_key(key)
    except (ValueError, binascii.Error):
        try:
            to_checksum_address(key)
        except (ValueError, binascii.Error):
            return None
        else:
            return Acct(None, key)
    else:
        return account


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


def load_json(file: str) -> dict:
    assert os.path.exists(file)
    with open(file, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as err:
            print('[!] Error parsing %s: %s: ' % (file, err))
            return {}


def dump_json(file: str, object: (dict, list)) -> None:
    if not file:
        file = f'unamed'
    with open(file, 'w') as f:
        json.dump(object, f)
