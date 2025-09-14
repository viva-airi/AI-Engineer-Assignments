"""
Google Meet クライアントのテストスクリプト
"""

import subprocess
import sys
import json
from datetime import datetime, timedelta


def test_google_meet_client():
    """Google Meet クライアントのテストを実行"""
    
    print("Google Meet クライアントのテストを開始...")
    
    # テスト用の日時を設定（1時間後から2時間後）
    now = datetime.now()
    start_time = now + timedelta(hours=1)
    end_time = now + timedelta(hours=2)
    
    # テストコマンドを構築
    cmd = [
        sys.executable, 'google_meet_client.py',
        '--title', 'テスト会議',
        '--start', start_time.strftime('%Y-%m-%d %H:%M'),
        '--end', end_time.strftime('%Y-%m-%d %H:%M'),
        '--description', 'これはテスト用のGoogle Meet会議です',
        '--attendees', 'test@example.com,test2@example.com',
        '--verbose'
    ]
    
    print(f"実行コマンド: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        # コマンドを実行
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
        
        print("標準出力:")
        print(result.stdout)
        
        if result.stderr:
            print("標準エラー:")
            print(result.stderr)
        
        print(f"終了コード: {result.returncode}")
        
        # 成功した場合、JSON出力を解析
        if result.returncode == 0 and result.stdout:
            try:
                output_data = json.loads(result.stdout)
                print("\n解析された出力:")
                print(json.dumps(output_data, ensure_ascii=False, indent=2))
                
                # 必要なフィールドが含まれているかチェック
                required_fields = ['eventId', 'htmlLink', 'meetUrl', 'start', 'end', 'timeZone']
                missing_fields = [field for field in required_fields if field not in output_data]
                
                if missing_fields:
                    print(f"警告: 以下のフィールドが不足しています: {missing_fields}")
                else:
                    print("✓ すべての必要なフィールドが含まれています")
                
            except json.JSONDecodeError as e:
                print(f"JSON解析エラー: {e}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"テスト実行エラー: {e}")
        return False


if __name__ == "__main__":
    success = test_google_meet_client()
    if success:
        print("\n✓ テストが正常に完了しました")
    else:
        print("\n✗ テストが失敗しました")
        sys.exit(1)
