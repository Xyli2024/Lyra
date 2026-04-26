"""Offline keyword-based mood/theme analysis.

Each category has English + common Mandarin keywords so the tagger works
for both Western and C-pop songs without any API calls.
"""
from typing import Dict, List, Tuple

_MOODS: Dict[str, List[str]] = {
    "love":         ["love", "heart", "kiss", "baby", "darling", "forever", "romance",
                     "爱", "心", "亲吻", "宝贝", "永远", "思念", "想你", "爱情"],
    "sad":          ["cry", "tears", "alone", "broken", "hurt", "miss", "pain", "goodbye",
                     "哭", "泪", "孤单", "心碎", "痛", "再见", "失去", "离开", "难过"],
    "happy":        ["happy", "joy", "smile", "dance", "party", "fun", "sunshine", "celebrate",
                     "快乐", "开心", "笑", "跳舞", "欢乐", "幸福", "高兴"],
    "peaceful":     ["peace", "calm", "gentle", "quiet", "still", "breathe", "rest",
                     "平静", "宁静", "轻柔", "安静", "自由", "放松"],
    "nostalgic":    ["remember", "memory", "past", "used to", "back then", "childhood",
                     "记忆", "回忆", "过去", "从前", "那年", "曾经", "时光"],
    "motivational": ["rise", "stronger", "believe", "dream", "never give up", "power", "fight",
                     "奋斗", "相信", "梦想", "坚持", "力量", "勇气", "拼搏"],
    "angry":        ["hate", "anger", "rage", "war", "destroy", "burn",
                     "恨", "愤怒", "战争", "仇恨"],
}


def analyze_mood(lyrics: str) -> Dict[str, int]:
    """Return keyword hit-counts per mood category (only non-zero entries)."""
    text = lyrics.lower()
    return {
        mood: score
        for mood, kws in _MOODS.items()
        if (score := sum(text.count(kw) for kw in kws)) > 0
    }


def top_mood(lyrics: str) -> str:
    scores = analyze_mood(lyrics)
    return max(scores, key=scores.__getitem__) if scores else "unknown"


def top_moods(lyrics: str, n: int = 3) -> List[Tuple[str, int]]:
    scores = analyze_mood(lyrics)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]
