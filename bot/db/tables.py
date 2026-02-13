from sqlalchemy import (
    Table, Column, Integer, BigInteger, String, Boolean,
    TIMESTAMP, Text, ForeignKey, CheckConstraint, MetaData
)
from sqlalchemy.sql import func

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("telegram_id", BigInteger, nullable=False, unique=True),
    Column("username", String(256), nullable=False),
    Column("chat_id", BigInteger, nullable=False),
    Column("phone_number", String(20), nullable=True),
    Column("is_subscribed", Boolean, nullable=False, server_default="FALSE"),
    Column("is_got_reward_for_subscription", Boolean, nullable=False, server_default="FALSE"),
    Column("created_at", TIMESTAMP, nullable=False, server_default=func.current_timestamp()),
)

# ------------------------------------------------------------
# assistance_requests – добавлены status и text
# ------------------------------------------------------------
assistance_requests = Table(
    "assistance_requests",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("request_type", String(256), nullable=False),
    Column("text", Text, nullable=True),                       # текст обращения
    Column("created_at", TIMESTAMP, nullable=False, server_default=func.current_timestamp()),
    Column("is_processed", Boolean, nullable=False, server_default="FALSE"),
    Column("processed_at", TIMESTAMP, nullable=True),
    Column("status", String(50), nullable=False, server_default="new"),
    Column("admin_comment", Text, nullable=True),             # не используется, оставлено
)

# ------------------------------------------------------------
# rewards – добавлены status и text
# ------------------------------------------------------------
rewards = Table(
    "rewards",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("link", String(512), nullable=True),               # ссылка на отзыв
    Column("text", Text, nullable=True),                     # текст отзыва (если есть)
    Column("is_paid", Boolean, nullable=False, server_default="FALSE"),
    Column("processed_at", TIMESTAMP, nullable=True),
    Column("created_at", TIMESTAMP, nullable=False, server_default=func.current_timestamp()),
    Column("status", String(50), nullable=False, server_default="new"),
    Column("admin_comment", Text, nullable=True),
)

# ------------------------------------------------------------
# messages_texts
# ------------------------------------------------------------
messages_texts = Table(
    "messages_texts",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("message_key", String(256), nullable=False, unique=True),
    Column("text", Text, nullable=False),
)

# ------------------------------------------------------------
# media_messages – только для файлов (фото, видео, документы)
# ------------------------------------------------------------
media_messages = Table(
    "media_messages",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("assistance_request_id", Integer, ForeignKey("assistance_requests.id", ondelete="CASCADE"), nullable=True),
    Column("reward_id", Integer, ForeignKey("rewards.id", ondelete="CASCADE"), nullable=True),
    Column("chat_id", BigInteger, nullable=False),
    Column("message_id", BigInteger, nullable=False),
    Column("media_group_id", String(256), nullable=True),
    Column("created_at", TIMESTAMP, nullable=False, server_default=func.current_timestamp()),
    CheckConstraint(
        "(assistance_request_id IS NOT NULL) OR (reward_id IS NOT NULL)",
        name="ck_media_messages_has_owner"
    )
)

# ------------------------------------------------------------
# request_comments – история комментариев
# ------------------------------------------------------------
request_comments = Table(
    "request_comments",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("request_type", String(20), nullable=False),
    Column("request_id", Integer, nullable=False),
    Column("admin_id", BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    Column("comment", Text, nullable=False),
    Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
)

settings = Table(
    "settings",
    metadata,
    Column("key", String(255), primary_key=True, nullable=False),
    Column("value", Text, nullable=False),
)