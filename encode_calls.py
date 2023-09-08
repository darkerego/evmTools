import eth_abi
import web3
from web3 import Web3
from utils.init_w3 import setup_w3
import json
ABI = json.loads("""[{"inputs":[{"internalType":"string","name":"reason","type":"string"},{"internalType":"address","name":"msgSender","type":"address"},{"internalType":"address","name":"txOrigin","type":"address"}],"name":"CallFailedError","type":"error"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"string","name":"reason","type":"string"}],"name":"CallFailed","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"string","name":"reason","type":"string"}],"name":"CallSuccess","type":"event"},{"inputs":[],"name":"CHANGE_SEL","outputs":[{"internalType":"bytes4","name":"","type":"bytes4"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"WRAP_CHANGE_SEL","outputs":[{"internalType":"bytes4","name":"","type":"bytes4"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_value","type":"uint256"}],"name":"changeState","outputs":[{"internalType":"bool","name":"success","type":"bool"},{"internalType":"string","name":"reason","type":"string"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"incrementer","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"oldValue","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"originalValue","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"testFunc","outputs":[{"internalType":"bool","name":"success","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_value","type":"uint256"}],"name":"wrapChangeState","outputs":[{"internalType":"bool","name":"success","type":"bool"},{"internalType":"bytes","name":"ret","type":"bytes"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_value","type":"uint256"}],"name":"wrapChangeStateView","outputs":[{"internalType":"bool","name":"success","type":"bool"}],"stateMutability":"view","type":"function"}]""")
SIM_ABI = json.loads('[{"inputs": [], "stateMutability": "nonpayable", "type": "constructor"}, {"inputs": [], "name": "SLOT_BAM", "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "SLOT_BAR", "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "SLOT_BAZ", "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "SLOT_FOO", "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "SLOT_FOOBAR", "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "SLOT_QUX", "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "uint256", "name": "offset", "type": "uint256"}, {"internalType": "uint256", "name": "length", "type": "uint256"}], "name": "getStorageAt", "outputs": [{"internalType": "bytes", "name": "", "type": "bytes"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "uint64", "name": "bam_", "type": "uint64"}], "name": "setBam", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "uint128", "name": "bar_", "type": "uint128"}], "name": "setBar", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "uint256[]", "name": "baz_", "type": "uint256[]"}], "name": "setBaz", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "uint256", "name": "foo_", "type": "uint256"}], "name": "setFoo", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "uint256", "name": "foo_", "type": "uint256"}, {"internalType": "uint256", "name": "bar_", "type": "uint256"}], "name": "setFoobar", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "uint256", "name": "key", "type": "uint256"}, {"internalType": "uint256", "name": "value", "type": "uint256"}], "name": "setQuxKeyValue", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "address", "name": "targetContract", "type": "address"}, {"internalType": "bytes", "name": "calldataPayload", "type": "bytes"}], "name": "simulate", "outputs": [{"internalType": "bytes", "name": "response", "type": "bytes"}], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "address", "name": "targetContract", "type": "address"}, {"internalType": "bytes", "name": "calldataPayload", "type": "bytes"}], "name": "simulateAndRevert", "outputs": [], "stateMutability": "nonpayable", "type": "function"}]')
def encode_function_call(function_signature: str, param_types: list, params: list) -> str:
    if len(param_types) != len(params):
        raise ValueError("Length of param_types and params should be the same")

    # Get the function selector
    function_selector = Web3.keccak(text=function_signature)[:4].hex()
    print('selector', function_selector)

    # Encode the parameters
    if params:
        # ABI-encode the parameters
        encoded_params = Web3.to_hex(eth_abi.encode(param_types, params))

        # Remove the '0x' prefix from the encoded parameters
        encoded_params = encoded_params[2:]

        # Construct the full encoded function call
        encoded_function_call = function_selector + encoded_params
    else:
        # If there are no parameters, the encoded function call is just the function selector
        encoded_function_call = function_selector

    return encoded_function_call

w3: web3.Web3 = setup_w3('goerli')

# Test the function with different inputs

change_state_call = encode_function_call("changeState(uint256)", ['uint256'], [100])  # One uint256 and one address parameter
wrap_state_call = encode_function_call("wrapChangeState(uint256)", ['uint256'], [1])  # Function without parameters

test_contract = w3.eth.contract(w3.to_checksum_address('0xe6442e7833C65e8e7CA6b420002897Bfeeea9693'), abi=ABI)
sim_contract = w3.eth.contract(w3.to_checksum_address('0x339c091049b7C57e18Ac72f9B68dE1A34EE0223c'), abi=SIM_ABI)

