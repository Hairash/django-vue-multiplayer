import asyncio
import httpx

client = httpx.AsyncClient(http2=True)


async def make_request():
    response = await client.get('http://localhost:8443/')
    print(response.text)

if __name__ == '__main__':
    asyncio.run(make_request())
