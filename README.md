# EvmTools

### About 

<p>
This is a colletion of various command line tools that I have written to interact with the EVM. This is far from 
complete, I probably have dozens, if not hundreds more little python programs like these that I intend on adding to 
this repository. 
</p>

<p>
This repository exists for two reasons. First, because I am sure that these utils will help others. And second, 
because I am trying to build a portfolio in order to make myself more marketable.
Reach out to me at chevisyoung at gmail dotkom if you'd like to hire me. I specialize in 
security, blockchain, particularly the Ethereum Virtual Machine.
</p>


#### Tools 

<p>
So far, I have included: 
</p>

- compute_contract_address.py 
  - computes the contract address for a certain account and supplied nonce
- mkey.py
  - Toolkit for parsing mnemonics into private keys
- nonceCheck.py 
  - Take a list of keys/addresses and grabs the nonces. Reports if any are higher than 0.
- read_contract_storage.py
  - It just reads values from a contract's storage
- token_scanner.py
  - This tool takes a list of accounts and then grabs from an indexer like bscscan.com a list of every ERC20 transfer event 
   that this account has ever been the recipient or sender of. Then, it checks to see if that account has positive balance for 
   each given token. It's basically the hackiest, but also the most thorough way to scan for tokens without having to use some 
   expensive, advanced api service.
- tx_decoder.py
  - Given a raw contract call tx data (bytecode raw data), figure out what each parameter is and what possible data 
   types each parameter may be. useful for reverse engineeering smart contracts that you don't have the source /abi for.
- uni2quote.py
  - Takes the ouput from the token_scanner.py and then queries a uniswap v2 router (currently supporting pancakeswapv2 and mdex on heco). 
    reports if any of the tokens are worth anything (can be traded for actual money). Beware that you will need to do your own honeypot 
    filtering (although I do have tools for that which I need to upload too!)
- zrxswap.py
  - Command line tool to interact with ZRX liquidity aggregator. It can provide quotes and do swaps.
  - TODO: redo argparse to make it easier to use with subparsers. Add support for more networks.
  - Note: ZRX now requires an API key to use and you need a "business email" to get one ... in other words, you need 
    to register a domain and set up email forwarding and then use that account in order to get a key ... </eyeroll> ,
    it is kind of a pain in the ass. Furthermore, the API is now rate limited to hell, so good luck. Oh and OneInch 
    just did the same thing, but they are even worse, as I could not figure out how to get any API key at all. Great  
    job ruining something awesome, guys ... 

#### Configuration
<p>
All that needs to be done is you need to set up your .env file. The way my tools look for these env variables is like:
</p>

<pre>
ethereum_http_endpoint = https://whatever.infura/whatever
ethereum_ws_endpoint = wss://whatever.whatever/whatever
</pre>

<p>
So, %s_http_endpoint and %s_ws_endpoint % (network name)
</p>