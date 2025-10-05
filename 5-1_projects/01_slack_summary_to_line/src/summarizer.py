"""
OpenAI要約機能
"""
from typing import List, Dict, Any
import openai
from openai import OpenAI


class Summarizer:
    def __init__(self, api_key: str):
        """
        OpenAI要約クライアントを初期化
        
        Args:
            api_key: OpenAI API Key
        """
        self.client = OpenAI(api_key=api_key)
    
    def summarize(self, messages: List[Dict[str, Any]]) -> str:
        """
        メッセージリストを要約
        
        Args:
            messages: Slackメッセージのリスト
            
        Returns:
            要約されたテキスト（最大500字、日本語）
            
        Raises:
            Exception: OpenAI API呼び出しでエラーが発生した場合
        """
        if not messages:
            return "直近のメッセージはありません。"
        
        # メッセージをテキストに変換
        message_texts = []
        for msg in messages:
            text = msg.get('text', '').strip()
            if text:
                # ユーザーIDをマスク
                user = msg.get('user', 'unknown')
                message_texts.append(f"[{user}]: {text}")
        
        if not message_texts:
            return "有効なメッセージがありません。"
        
        # メッセージを結合（長すぎる場合は切り詰め）
        combined_text = "\n".join(message_texts)
        if len(combined_text) > 4000:  # トークン制限を考慮
            combined_text = combined_text[:4000] + "..."
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "あなたはSlackメッセージの要約アシスタントです。以下のメッセージを要点を箇条書きで要約してください。最大500文字で、日本語で回答してください。重要な情報や決定事項、質問、回答などを中心にまとめてください。"
                    },
                    {
                        "role": "user",
                        "content": f"以下のSlackメッセージを要約してください：\n\n{combined_text}"
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            
            # 500文字制限を適用
            if len(summary) > 500:
                summary = summary[:497] + "..."
            
            return summary
            
        except Exception as e:
            raise Exception(f"OpenAI要約処理でエラーが発生しました: {str(e)}")
