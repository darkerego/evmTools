#!/usr/bin/env python3
import argparse
import binascii
import hashlib
import hmac
import struct
import web3
import os
from base58 import b58encode_check
from ecdsa.curves import SECP256k1

# from lib import style
BIP39_PBKDF2_ROUNDS = 2048
BIP39_SALT_MODIFIER = "mnemonic"
BIP32_PRIVDEV = 0x80000000
BIP32_CURVE = SECP256k1
BIP32_SEED_MODIFIER = b'Bitcoin seed'
LEDGER_ETH_DERIVATION_PATH = "m/44'/60'/0'/0"
alt_paths = ["m/0'/0'", "m/44'/60'/0'/0", "m/44'/60'/0'/0", "m/0'/0", "m/44'/0'/0'", "m/49'/0'/0'/0", "m/84'/0'/0'/0",
             "m/44'/60'/0'", "m/44'/60'/0/0",
             "m/0'/60'/0'/0", "m/44'/60'/0'/0"]


class ColorPrint:
    def __init__(self):
        self.color_map: list[tuple] = [('red', 91), ('green', 92), ('yellow', 93), ('blue', 94),
                                       ('pink', 95), ('teal', 96), ('white', 97), ('reset', 0)]
        self.iterate()

    def color(self, n: int):
        return f"\u001b[{n}m"

    @property
    def end(self):
        return "\u001b[0m"

    def iterate(self):
        for x in self.color_map:
            setattr(self, x[0], self.color(x[1]))
            # print(self.color(x[1]) + x[0] + self.end)


def mnemonic_to_bip39seed(mnemonic: str, passphrase: str):
    """ BIP39 seed from a mnemonic key.
        Logic adapted from https://github.com/trezor/python-mnemonic. """
    mnemonic = bytes(mnemonic, 'utf8')
    salt = bytes(BIP39_SALT_MODIFIER + passphrase, 'utf8')
    return hashlib.pbkdf2_hmac('sha512', mnemonic, salt, BIP39_PBKDF2_ROUNDS)


def bip39seed_to_bip32masternode(seed: bytes):
    """ BIP32 master node derivation from a bip39 seed.
        Logic adapted from https://github.com/satoshilabs/slips/blob/master/slip-0010/testvectors.py. """
    k = seed
    h = hmac.new(BIP32_SEED_MODIFIER, seed, hashlib.sha512).digest()
    key, chain_code = h[:32], h[32:]
    return key, chain_code


def derive_public_key(private_key: bytes):
    """ Public key from a private key.
        Logic adapted from https://github.com/satoshilabs/slips/blob/master/slip-0010/testvectors.py. """

    Q = int.from_bytes(private_key, byteorder='big') * BIP32_CURVE.generator
    xstr = Q.x().to_bytes(32, byteorder='big')
    parity = Q.y() & 1
    return (2 + parity).to_bytes(1, byteorder='big') + xstr


def derive_bip32childkey(parent_key: any, parent_chain_code: bytes, i: any):
    """ Derives a child key from an existing key, i is current derivation parameter.
        Logic adapted from https://github.com/satoshilabs/slips/blob/master/slip-0010/testvectors.py. """

    assert len(parent_key) == 32
    assert len(parent_chain_code) == 32
    k = parent_chain_code
    if (i & BIP32_PRIVDEV) != 0:
        key = b'\x00' + parent_key
    else:
        key = derive_public_key(parent_key)
    d = key + struct.pack('>L', i)
    while True:
        h = hmac.new(k, d, hashlib.sha512).digest()
        key, chain_code = h[:32], h[32:]
        a = int.from_bytes(key, byteorder='big')
        b = int.from_bytes(parent_key, byteorder='big')
        key = (a + b) % BIP32_CURVE.order
        if a < BIP32_CURVE.order and key != 0:
            key = key.to_bytes(32, byteorder='big')
            break
        d = b'\x01' + h[32:] + struct.pack('>L', i)

    return key, chain_code


def fingerprint(public_key: str):
    """ BIP32 fingerprint formula, used to get b58 serialized key. """

    return hashlib.new('ripemd160', hashlib.sha256(public_key).digest()).digest()[:4]


def b58xprv(parent_fingerprint, private_key, chain, depth, childnr):
    """ Private key b58 serialization format. """

    raw = (
            b'\x04\x88\xad\xe4' +
            bytes(chr(depth), 'utf-8') +
            parent_fingerprint +
            childnr.to_bytes(4, byteorder='big') +
            chain +
            b'\x00' +
            private_key)

    return b58encode_check(raw)


def b58xpub(parent_fingerprint, public_key, chain, depth, childnr):
    """ Public key b58 serialization format. """

    raw = (
            b'\x04\x88\xb2\x1e' +
            bytes(chr(depth), 'utf-8') +
            parent_fingerprint +
            childnr.to_bytes(4, byteorder='big') +
            chain +
            public_key)

    return b58encode_check(raw)


def parse_derivation_path(str_derivation_path):
    """ Parses a derivation path such as "m/44'/60/0'/0" and returns
        list of integers for each element in path. """

    path = []
    if str_derivation_path[0:2] != 'm/':
        raise ValueError("Can't recognize derivation path. It should look like \"m/44'/60/0'/0\".")

    for i in str_derivation_path.lstrip('m/').split('/'):
        if "'" in i:
            try:
                path.append(BIP32_PRIVDEV + int(i[:-1]))
            except ValueError:
                pass

        else:
            path.append(int(i))
    return path


def mnemonic_to_private_key(mnemonic, str_derivation_path=LEDGER_ETH_DERIVATION_PATH, passphrase="", index=0):
    """ Performs all convertions to get a private key from a mnemonic sentence, including:

            BIP39 mnemonic to seed
            BIP32 seed to master key
            BIP32 child derivation of a path provided

        Parameters:
            mnemonic -- seed wordlist, usually with 24 words, that is used for ledger wallet backup
            str_derivation_path -- string that directs BIP32 key derivation, defaults to path
                used by ledger ETH wallet
    """
    if index == 0:
        dp2 = str_derivation_path
    else:
        index = index - 1
        dp2 = str_derivation_path
        dp2 += f'/{index}'

    # dp2 = dp2[:-1]
    # print(dp2)
    derivation_path = parse_derivation_path(dp2)

    bip39seed = mnemonic_to_bip39seed(mnemonic, passphrase)

    master_private_key, master_chain_code = bip39seed_to_bip32masternode(bip39seed)

    private_key, chain_code = master_private_key, master_chain_code

    for i in derivation_path:
        private_key, chain_code = derive_bip32childkey(private_key, chain_code, i)

    return private_key


def read_as_lines(file: str):
    lines_list = []
    with open(file) as f:
        f = f.readlines()
        for x in f:
            lines_list.append(x.strip('\r\n'))
    return lines_list


def generate(mnemonic, path=LEDGER_ETH_DERIVATION_PATH, passphrase="", children=3):
    print('MNEMONIC: ', mnemonic)
    print('PATH: ', path)
    private_key = mnemonic_to_private_key(mnemonic, path, passphrase)
    acct = web3.Account.from_key(private_key)
    address = acct.address
    print("# Your private key is: {}".format(str(binascii.hexlify(private_key), 'utf-8')))
    if args.output:
        log_key(private_key)
    print(f'Address: {address}')
    print('Child keys: ')
    for x in range(0, children):
        private_key = mnemonic_to_private_key(mnemonic, index=x)
        acct = web3.Account.from_key(private_key)
        address = acct.address
        if args.output:
            log_key(private_key)
            print("# Your private key is: {}".format(str(binascii.hexlify(private_key), 'utf-8')))
            print(f' Index {x} , Address: {address}')
        else:
            acct = web3.Account.from_key(private_key)
            address = acct.address

            print("# Your private key is: {}".format(str(binascii.hexlify(private_key), 'utf-8')))
            print(f' Index {x} , Address: {address}')


def log_key(k):
    with open(args.output, 'a') as f:
        k = str(binascii.hexlify(k), 'utf-8')
        f.write(str(k) + '\n')


if __name__ == '__main__':

    args = argparse.ArgumentParser()
    # args.add_argument('-f', '--file', type=str, required=False, help='The file with memnonic')
    # args.add_argument('-s', '--string', type=str)
    args.add_argument('file_or_string', type=str, default=None, help='Mnemonic string or list of mnemonics')
    args.add_argument('-o', '--output', type=str, default=None)
    args.add_argument('-c', '--children', type=int, default=3, help='Show the next n child keys.')
    args.add_argument('-ep', '--extended-paths', dest='extended_paths', action='store_true',
                      help='Try extensive derivation path list.')
    args.add_argument('-p', '--password', default="", help='Specify a password for seed.')
    args = args.parse_args()

    if args.file_or_string is not None:
        if os.path.exists(args.file_or_string):
            mnemonics = read_as_lines(args.file_or_string)
        else:
            mnemonics = [args.file_or_string]

        for mnemonic in mnemonics:
            if args.extended_paths:
                extended_paths = alt_paths
                for path in extended_paths:
                    generate(mnemonic, path, args.password, children=args.children)
            else:
                generate(mnemonic, LEDGER_ETH_DERIVATION_PATH, args.password, args.children)
    else:
        print('[!] Please supply either a string mnemonic, or a file with list of string mnemonics.')