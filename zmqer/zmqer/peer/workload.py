import asyncio
from random import randint


async def workload(input):
    await asyncio.sleep(1.0)

    output = f"SomeData={input}"
    return output


async def json_workload():
    await asyncio.sleep(1.0)

    output = {"random": randint(1, 100)}
    return output
