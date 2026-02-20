import asyncio
from fastmcp import Client

MCP_URL = "https://mcp.mospi.gov.in"

async def main():
    async with Client(MCP_URL) as client:
        result = await client.call_tool(
            "3_get_metadata",
            {
                "dataset": "IIP",
                "base_year": "2011-12",
                "type": "Sectoral",
            },
        )
        print(result)

asyncio.run(main())
