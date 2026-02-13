import asyncio
from typing import *
from aiogram import BaseMiddleware
from aiogram.types import Message


class AlbumMiddleware(BaseMiddleware):
    def __init__(self, latency: Union[int, float] = 0.5):
        self.albums = {}
        self.latency = latency
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        if not event.media_group_id:
            return await handler(event, data)

        try:
            self.albums[event.media_group_id].append(event)
            return None
        except KeyError:
            self.albums[event.media_group_id] = [event]
            await asyncio.sleep(self.latency)

            data["album"] = self.albums.pop(event.media_group_id)

        return await handler(event, data)