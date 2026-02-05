CRONOS_RPC = "https://evm-t3.cronos.org"
CHAIN_ID = 338

CONTRACT_ADDRESS = "0x0C56559947C6eBa04aC158b462090f1383A3839A"

CRONOS_TESTNET_EXPLORER = "https://explorer.cronos.org/testnet"

def tx_link(tx_hash: str) -> str:
    return f"{CRONOS_TESTNET_EXPLORER}/tx/{tx_hash}"

def address_link(addr: str) -> str:
    return f"{CRONOS_TESTNET_EXPLORER}/address/{addr}"
