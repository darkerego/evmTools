#!/usr/bin/env python3

import os
import dotenv
import web3
from web3.exceptions import ExtraDataLengthError
from web3.middleware import geth_poa_middleware

from exceptions.errors import DotenvNotConfigured

dotenv.load_dotenv()


def is_poa_chain(w3: web3.Web3):
    try:
        genesis_block = w3.eth.get_block(0)
    except ExtraDataLengthError:
        return True
    else:
        extra_data = genesis_block['extraData']
        print(len(extra_data))
        consensus_engine = extra_data[0:4]
        if consensus_engine in (b'\x63\x6c\x69\x71', b'\x69\x62\x66\x74') or len(extra_data) > 64:
            return True
        else:
            return False


def setup_w3(network: str) -> (web3.Web3, False):
    endpoint = os.environ.get(f'{network}_http_endpoint')
    if endpoint is None:
        raise DotenvNotConfigured("You need to setup your `.env` file first! See docs.")
    w3 = web3.Web3(web3.HTTPProvider(endpoint))
    if w3.is_connected():
        if is_poa_chain(w3):
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return w3
    return False

