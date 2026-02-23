import asyncio
import uvicorn

from src.app import create_app

app = create_app()


async def run() -> None:
    config = uvicorn.Config(
        "main:app", host="127.0.0.1", port=8000, reload=False
    )
    server = uvicorn.Server(config=config)
    tasks = (
        asyncio.create_task(server.serve()),
    )

    await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
