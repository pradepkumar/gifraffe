import asyncio

def start_cleanup_task(settings):
    async def _noop():
        pass
    return asyncio.ensure_future(_noop())
