"""環境変数読み込みユーティリティ"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv


def load_env(env_path: Path) -> Dict[str, str]:
    """
    .envファイルから環境変数を読み込み、必要な設定値を返す
    
    Args:
        env_path: .envファイルの絶対パス
        
    Returns:
        必要な環境変数の辞書
        {
            "SLACK_BOT_TOKEN": str,
            "SLACK_CHANNEL_ID": str, 
            "LINE_CHANNEL_ACCESS_TOKEN": str,
            "LINE_TO_USER_ID": str
        }
        
    Raises:
        FileNotFoundError: .envファイルが存在しない場合
        ValueError: 必要な環境変数が設定されていない場合
    """
    if not env_path.exists():
        raise FileNotFoundError(f"環境設定ファイルが見つかりません: {env_path}")
    
    # .envファイルを読み込み
    load_dotenv(env_path)
    
    # 必要な環境変数を取得
    required_vars = {
        "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN"),
        "SLACK_CHANNEL_ID": os.getenv("SLACK_CHANNEL_ID"),
        "LINE_CHANNEL_ACCESS_TOKEN": os.getenv("LINE_CHANNEL_ACCESS_TOKEN"),
        "LINE_TO_USER_ID": os.getenv("LINE_TO_USER_ID"),
    }
    
    # 未設定の変数をチェック
    missing_vars = [key for key, value in required_vars.items() if not value]
    if missing_vars:
        raise ValueError(f"以下の環境変数が設定されていません: {', '.join(missing_vars)}")
    
    return required_vars


def get_env_path() -> Path:
    """
    プロジェクトルートから環境設定ファイルのパスを取得
    
    Returns:
        slack_line_mirror.env の絶対パス
    """
    # このファイルの場所を基準にプロジェクトルートを取得
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    
    # 4-2-2/env/slack_line_mirror.env のパスを構築
    env_path = project_root / "4-2-2" / "env" / "slack_line_mirror.env"
    
    return env_path


def print_env_setup_help():
    """環境設定のヘルプメッセージを表示"""
    env_path = get_env_path()
    example_path = env_path.parent / "slack_line_mirror.env.example"
    
    print(f"環境設定ファイルが見つかりません: {env_path}")
    print(f"以下のファイルを参考に設定してください: {example_path}")
    print("\n必要な環境変数:")
    print("- SLACK_BOT_TOKEN: Slack Bot Token")
    print("- SLACK_CHANNEL_ID: 監視するSlackチャンネルID (Cで始まる)")
    print("- LINE_CHANNEL_ACCESS_TOKEN: LINE Messaging API Channel Access Token")
    print("- LINE_TO_USER_ID: 通知先のLINEユーザーID")


if __name__ == "__main__":
    # テスト用
    try:
        env_path = get_env_path()
        print(f"環境設定ファイルパス: {env_path}")
        env_vars = load_env(env_path)
        print("環境変数読み込み成功:")
        for key, value in env_vars.items():
            # セキュリティのため、トークンの一部のみ表示
            display_value = value[:8] + "..." if len(value) > 8 else value
            print(f"  {key}: {display_value}")
    except Exception as e:
        print(f"エラー: {e}")
        print_env_setup_help()
