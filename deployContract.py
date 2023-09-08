import json
import os.path

import web3
from eth_account.signers.local import LocalAccount
from solc import compile_standard

import argparse
import utils.init_w3
from utils.helpers import load_json


class ContractDeployer:
    def __init__(self, network: str, account: LocalAccount):
        self.network = network
        self.account = account
        self.w3: web3.Web3 = utils.init_w3.setup_w3(network)


    def compile_contract(self, file: str) -> dict:
        # # solc --bin --abi -o output_folder your_contract.sol
        ret = compile_standard({'language': 'Solidity', 'sources': {file:  {'urls': [file]}},
                                "settings": {
                                    "outputSelection": {
                                        "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
                                    }
                                }})

        return ret

    def deploy(self, solidity_json: dict):
        contract_fname = list(solidity_json.get('contracts').keys())[0]
        _bytecode = solidity_json.get('contracts')[contract_fname]
        key = list(_bytecode.keys())[0]
        bytecode = _bytecode[key]["evm"]["bytecode"]["object"]
        abi = json.loads(
            solidity_json["contracts"][contract_fname][key]["metadata"]
        )["output"]["abi"]
        # Create contract factory
        contract = self.w3.eth.contract(abi=abi, bytecode=bytes(bytecode.encode()))
        gas_estimate = contract.constructor().estimate_gas()
        # Build transaction
        transaction = contract.constructor().build_transaction({
            'from': self.account.address,
            'gas': gas_estimate,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })
        # Sign transaction
        signed_transaction = self.w3.eth.account.signTransaction(transaction, self.account.key)
        # Send transaction
        transaction_hash = self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        # Get transaction receipt
        transaction_receipt = self.w3.eth.wait_for_transaction_receipt(transaction_hash)
        # Contract address
        contract_address = transaction_receipt['contractAddress']
        print(f'Contract deployed at address: {contract_address}')
        return contract_address


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('file', type=str)
    args.add_argument('-w', '--wallet', type=str, default='keys/default_wallet.json')
    args = args.parse_args()
    if not os.path.exists(args.wallet):
        print('[!] You need to configure your wallet first. See the docs.')
    wallet = load_json(args.wallet)
    api=ContractDeployer('ganache', None)
    print(api.compile_contract('Test.sol'))
