import requests
from demeter import TokenInfo


class Pool:
    POOL_QUERY = """query get_pools($pool_id: ID!) {
        pools(where: {id: $pool_id}) {
            tick
            sqrtPrice
            liquidity
            feeTier
            totalValueLockedUSD
            totalValueLockedETH
            token0 {
                symbol
                decimals
            }
            token1 {
                symbol
                decimals
            }
        }
    }"""

    def __init__(self, pool_address: str, api_key: str):
        self.pool_address = pool_address
        self.api_key = api_key
        self.load_pool_data()

    def load_pool_data(self):
        data = self.fetch_data_subgraph(self.POOL_QUERY, {"pool_id": self.pool_address}, "pools")[0]

        self.token0 = str(data["token0"]["symbol"])
        self.token1 = str(data["token1"]["symbol"])
        self.decimals0 = int(data["token0"]["decimals"])
        self.decimals1 = int(data["token1"]["decimals"])
        self.fee_tier_bps = int(data["feeTier"])
        self.fee_tier = int(data["feeTier"]) / 1e6
        self.tick_spacing = self.fee_tier_to_tick_spacing()
        self.sqrt_price_x96 = int(data["sqrtPrice"])
        self.liquidity = int(data["liquidity"])
        self.tick = int(data["tick"])
        self.total_value_locked_usd = float(data["totalValueLockedUSD"])
        self.total_value_locked_eth = float(data["totalValueLockedETH"])

        # self.token0 = TokenInfo(name=self.token0, decimal=self.decimals0)
        # self.token1 = TokenInfo(name=self.token1, decimal=self.decimals1)

        self.q96 = 2**96

    def fee_tier_to_tick_spacing(self):
        return {100: 1, 500: 10, 3000: 60, 10000: 200}.get(self.fee_tier, 60)

    def fetch_data_subgraph(self, query, variables=None, data_key=None):
        url = f"https://gateway-arbitrum.network.thegraph.com/api/{self.api_key}/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
        response = requests.post(url, json={"query": query, "variables": variables})
        if response.status_code != 200:
            raise RuntimeError(
                f"Query failed. Status code: {response.status_code}. Response: {response.text}"
            )
        result = response.json()
        return result["data"][data_key] if data_key else result["data"]

    def __str__(self):
        return f"""
Pool Address: {self.pool_address}
Token Pair: {self.token0}/{self.token1}
Decimals token1: {self.decimals0}
Decimals token2: {self.decimals1}
Fee Tier: {self.fee_tier}
Tick Spacing: {self.tick_spacing}
Current Tick: {self.tick}
Current Sqrt Price: {self.sqrt_price_x96}
Liquidity: {self.liquidity}
Total Value Locked (USD): ${self.total_value_locked_usd:.2f}
Total Value Locked (ETH): {self.total_value_locked_eth:.6f} ETH
                """
