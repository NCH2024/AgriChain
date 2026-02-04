CRONOS_RPC = "https://evm-t3.cronos.org"
CHAIN_ID = 338

CONTRACT_ADDRESS = "0x1228BC01B160D2da1932dc378C9c8689F002a9b7"

CRONOS_TESTNET_EXPLORER = "https://explorer.cronos.org/testnet"

def tx_link(tx_hash: str) -> str:
    return f"{CRONOS_TESTNET_EXPLORER}/tx/{tx_hash}"

def address_link(addr: str) -> str:
    return f"{CRONOS_TESTNET_EXPLORER}/address/{addr}"
