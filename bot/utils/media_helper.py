from aiogram.types import Message

def extract_media_info(message: Message) -> dict:
    info = {
        "chat_id": message.chat.id,
        "message_id": message.message_id,
        "media_group_id": message.media_group_id,
        "caption": message.caption or message.text,
        "file_id": None,
        "content_type": "unknown"
    }

    if message.photo:
        info["file_id"] = message.photo[-1].file_id
        info["content_type"] = "photo"
    elif message.document:
        info["file_id"] = message.document.file_id
        info["content_type"] = "document"
    elif message.video:
        info["file_id"] = message.video.file_id
        info["content_type"] = "video"
    elif message.audio:
        info["file_id"] = message.audio.file_id
        info["content_type"] = "audio"
    elif message.voice:
        info["file_id"] = message.voice.file_id
        info["content_type"] = "voice"
    elif message.text:
        info["file_id"] = None
        info["content_type"] = "text"
    return info