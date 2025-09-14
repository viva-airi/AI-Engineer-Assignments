#!/usr/bin/env python3
"""
Google Drive API クライアント
ファイルアップロード機能付き
"""

import os
import sys
import json
import argparse
import mimetypes
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError

# Google Drive API のスコープ
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# 設定
CREDENTIALS_FILE = 'credentials/google_credentials.json'
TOKEN_FILE = 'tokens/token.json'

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GoogleDriveClient:
    """Google Drive API クライアント"""
    
    def __init__(self, verbose: bool = False):
        """
        初期化
        
        Args:
            verbose (bool): 詳細ログを有効にするか
        """
        self.verbose = verbose
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Google Drive API認証を実行"""
        creds = None
        
        # token.jsonファイルが存在するかチェック
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        # 有効な認証情報がない場合、ユーザーにログインを求める
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                if self.verbose:
                    logger.info("認証トークンを更新中...")
                creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    raise FileNotFoundError(f"認証情報ファイルが見つかりません: {CREDENTIALS_FILE}")
                
                if self.verbose:
                    logger.info("ブラウザで認証を行います...")
                
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # 認証情報を保存
            os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            
            if self.verbose:
                logger.info(f"認証情報を保存しました: {TOKEN_FILE}")
        
        self.service = build('drive', 'v3', credentials=creds)
    
    def _get_mime_type(self, file_path: str, specified_mime: Optional[str] = None) -> str:
        """
        MIMEタイプを取得
        
        Args:
            file_path (str): ファイルパス
            specified_mime (str, optional): 指定されたMIMEタイプ
            
        Returns:
            str: MIMEタイプ
        """
        if specified_mime:
            return specified_mime
        
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            return mime_type
        
        # 拡張子から推定
        ext = Path(file_path).suffix.lower()
        mime_map = {
            '.txt': 'text/plain',
            '.py': 'text/x-python',
            '.js': 'text/javascript',
            '.html': 'text/html',
            '.css': 'text/css',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.pdf': 'application/pdf',
            '.zip': 'application/zip',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.svg': 'image/svg+xml',
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
        }
        
        return mime_map.get(ext, 'application/octet-stream')
    
    def _check_file_exists(self, file_path: str) -> bool:
        """
        ファイルの存在をチェック
        
        Args:
            file_path (str): ファイルパス
            
        Returns:
            bool: ファイルが存在するか
        """
        return os.path.isfile(file_path)
    
    def _check_folder_permission(self, folder_id: str) -> bool:
        """
        フォルダの権限をチェック
        
        Args:
            folder_id (str): フォルダID
            
        Returns:
            bool: フォルダにアクセス可能か
        """
        try:
            self.service.files().get(fileId=folder_id).execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                return False
            raise
    
    def _find_duplicate_file(self, name: str, folder_id: str) -> Optional[Dict[str, Any]]:
        """
        同名ファイルを検索
        
        Args:
            name (str): ファイル名
            folder_id (str): フォルダID
            
        Returns:
            Optional[Dict]: 重複ファイル情報（存在しない場合はNone）
        """
        try:
            query = f"name='{name}' and parents in '{folder_id}' and trashed=false"
            results = self.service.files().list(q=query, fields="files(id,name,mimeType,size)").execute()
            files = results.get('files', [])
            return files[0] if files else None
        except HttpError as e:
            if self.verbose:
                logger.error(f"重複ファイル検索エラー: {e}")
            return None
    
    def _handle_duplicate(self, duplicate_file: Dict[str, Any], if_exists: str, 
                         name: str) -> str:
        """
        重複ファイルの処理
        
        Args:
            duplicate_file (Dict): 重複ファイル情報
            if_exists (str): 重複時の処理方法
            name (str): 元のファイル名
            
        Returns:
            str: 最終的なファイル名
        """
        if if_exists == 'skip':
            if self.verbose:
                logger.info(f"同名ファイルが存在するためスキップします: {name}")
            return None
        elif if_exists == 'overwrite':
            if self.verbose:
                logger.info(f"同名ファイルを上書きします: {name}")
            return name
        elif if_exists == 'rename':
            # ファイル名に番号を付けてリネーム
            base_name = Path(name).stem
            extension = Path(name).suffix
            counter = 1
            
            while True:
                new_name = f"{base_name}_{counter}{extension}"
                if not self._find_duplicate_file(new_name, duplicate_file.get('parents', [''])[0]):
                    if self.verbose:
                        logger.info(f"ファイル名を変更します: {name} -> {new_name}")
                    return new_name
                counter += 1
        else:
            raise ValueError(f"無効な重複処理方法: {if_exists}")
    
    def upload_file(self, file_path: str, folder_id: str = None, 
                   name: str = None, mime_type: str = None, 
                   if_exists: str = 'rename') -> Dict[str, Any]:
        """
        ファイルをアップロード
        
        Args:
            file_path (str): アップロードするファイルのパス
            folder_id (str, optional): アップロード先フォルダID
            name (str, optional): アップロード後のファイル名
            mime_type (str, optional): MIMEタイプ
            if_exists (str): 重複時の処理方法 (rename|skip|overwrite)
            
        Returns:
            Dict: アップロード結果
        """
        try:
            # 前検証
            if not self._check_file_exists(file_path):
                raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
            
            if folder_id and not self._check_folder_permission(folder_id):
                raise PermissionError(f"フォルダにアクセスできません: {folder_id}")
            
            # ファイル名とMIMEタイプを決定
            if not name:
                name = os.path.basename(file_path)
            
            mime_type = self._get_mime_type(file_path, mime_type)
            
            if self.verbose:
                logger.info(f"ファイル: {file_path}")
                logger.info(f"ファイル名: {name}")
                logger.info(f"MIMEタイプ: {mime_type}")
                logger.info(f"フォルダID: {folder_id}")
            
            # 重複チェック
            if folder_id:
                duplicate = self._find_duplicate_file(name, folder_id)
                if duplicate:
                    final_name = self._handle_duplicate(duplicate, if_exists, name)
                    if final_name is None:  # skip
                        return {
                            'status': 'skipped',
                            'message': f'同名ファイルが存在するためスキップしました: {name}'
                        }
                    name = final_name
            
            # ファイルサイズを取得
            file_size = os.path.getsize(file_path)
            
            # メタデータを準備
            file_metadata = {
                'name': name,
                'mimeType': mime_type
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # ファイルアップロード
            if file_size < 5 * 1024 * 1024:  # 5MB未満はmultipart
                if self.verbose:
                    logger.info("multipartアップロードを使用します")
                
                media = MediaFileUpload(file_path, mimetype=mime_type, resumable=False)
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,name,webViewLink,webContentLink,size,mimeType,createdTime,parents'
                ).execute()
            else:  # 5MB以上はresumable
                if self.verbose:
                    logger.info("resumableアップロードを使用します")
                
                media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,name,webViewLink,webContentLink,size,mimeType,createdTime,parents'
                ).execute()
            
            # 結果を整形
            result = {
                'fileId': file.get('id'),
                'name': file.get('name'),
                'webViewLink': file.get('webViewLink'),
                'webContentLink': file.get('webContentLink'),
                'sizeBytes': int(file.get('size', 0)),
                'mimeType': file.get('mimeType'),
                'createdTime': file.get('createdTime'),
                'folderId': file.get('parents', [None])[0] if file.get('parents') else None
            }
            
            if self.verbose:
                logger.info(f"アップロード完了: {result['fileId']}")
            
            return result
            
        except Exception as e:
            error_msg = f"アップロードエラー: {str(e)}"
            if self.verbose:
                logger.error(error_msg)
            raise Exception(error_msg)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='Google Drive ファイルアップロード')
    parser.add_argument('--path', required=True, help='アップロードするファイルのパス')
    parser.add_argument('--folder-id', help='アップロード先フォルダID')
    parser.add_argument('--name', help='アップロード後のファイル名')
    parser.add_argument('--mime', help='MIMEタイプ')
    parser.add_argument('--if-exists', choices=['rename', 'skip', 'overwrite'], 
                       default='rename', help='同名ファイルが存在する場合の処理方法')
    parser.add_argument('--verbose', action='store_true', help='詳細ログを表示')
    
    args = parser.parse_args()
    
    # ログレベル設定
    if args.verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)
    
    try:
        # クライアント初期化
        client = GoogleDriveClient(verbose=args.verbose)
        
        # ファイルアップロード
        result = client.upload_file(
            file_path=args.path,
            folder_id=args.folder_id,
            name=args.name,
            mime_type=args.mime,
            if_exists=args.if_exists
        )
        
        # 結果をJSONで出力
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        # エラーをstderrに出力
        print(f"エラー: {str(e)}", file=sys.stderr)
        print("対処方法:", file=sys.stderr)
        print("- ファイルパスが正しいか確認してください", file=sys.stderr)
        print("- フォルダIDが正しいか確認してください", file=sys.stderr)
        print("- 認証情報が正しいか確認してください", file=sys.stderr)
        print("- ネットワーク接続を確認してください", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
