#!/usr/bin/env python3
"""
テスト用ファイル作成スクリプト
"""

import os
import base64

def create_minimal_png():
    """最小のPNGファイルを作成（PILなし版）"""
    # 最小の1x1ピクセル透明PNGのBase64データ
    png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    # Base64をデコードしてPNGファイルとして保存
    png_data = base64.b64decode(png_base64)
    
    with open('test_minimal.png', 'wb') as f:
        f.write(png_data)
    
    print(f"最小PNGファイルを作成しました: {len(png_data)} bytes")

def create_test_txt():
    """テスト用テキストファイルを作成"""
    content = "これはテスト用のテキストファイルです。\nGoogle Drive API テスト用。"
    
    with open('test_file.txt', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"テストテキストファイルを作成しました: {len(content)} bytes")

if __name__ == '__main__':
    create_minimal_png()
    create_test_txt()
    print("テストファイルの作成が完了しました。")
