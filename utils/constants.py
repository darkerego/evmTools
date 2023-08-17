import web3


class Constants:
    zero_address = web3.Web3.to_checksum_address('0x' + '0'*40)
