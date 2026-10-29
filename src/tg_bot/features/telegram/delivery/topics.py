from codex_bot.base import UnifiedViewDTO, ViewResultDTO

TOPICS = {
    "tasks": 3,
    "game_design": 5,
    "lore": 7,
    "graphics": 9,
    "bugs": 12,
    "github": 14,
    "deploy": 16,
}


def topic_view(chat_id: int, topic: str, text: str) -> UnifiedViewDTO:
    """Create an explicitly addressed view; topic names are never inferred."""
    return UnifiedViewDTO(
        chat_id=chat_id,
        message_thread_id=TOPICS[topic],
        mode="topic",
        session_key=f"dev:{chat_id}:{TOPICS[topic]}",
        content=ViewResultDTO(text=text),
    )
