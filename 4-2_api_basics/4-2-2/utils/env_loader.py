from pathlib import Path
from dotenv import dotenv_values

def load_env(env_path: str) -> dict:
    """
    指定パスの .env を読み込み、dict で返す。
    例: env = load_env("4-2-2/env/youtube.env"); env["YOUTUBE_API_KEY"]
    """
    p = Path(env_path)
    if not p.exists():
        raise FileNotFoundError(f".env が見つかりません: {env_path}")
    return dotenv_values(env_path)
