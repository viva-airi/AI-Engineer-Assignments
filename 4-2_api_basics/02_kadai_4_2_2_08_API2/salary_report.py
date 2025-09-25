#!/usr/bin/env python3
"""
勤怠・時給・売上計算とLINE通知ツール
"""
import argparse
import csv
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import pytz

from dotenv import load_dotenv

# 👇 まずここでパスを追加する
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# そのあとで utils をimportする
from utils.sheets import (
    get_attendance, get_wages, get_sales, append_runlog, get_incomplete_rows
)
from utils.line import push_text


def load_environment():
    """環境変数を読み込み（同階層→親→親の親）"""
    env_paths = [
        BASE_DIR / '.env',
        BASE_DIR.parent / '.env',
        BASE_DIR.parent.parent / '.env'
    ]
    
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            print(f"[DEBUG] Loaded .env from: {env_path}")
            break
    
    # 必須環境変数のチェック
    required_vars = [
        'SPREADSHEET_ID', 'LINE_CHANNEL_ACCESS_TOKEN', 'LINE_TO_USER_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"[ERROR] Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(2)


def get_today_jst() -> str:
    """JST基準で今日の日付文字列を生成"""
    timezone = os.getenv('TIMEZONE', 'Asia/Tokyo')
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    return now.strftime('%Y/%m/%d')


def format_currency(amount: int) -> str:
    """金額をカンマ入り＋円でフォーマット"""
    return f"{amount:,}円"


def calculate_daily_salary(hours: float, wage: int) -> int:
    """日給を計算（円未満切り捨て）"""
    return math.floor(hours * wage)


def format_attendance_table(attendance_data: List[Dict], wages: Dict[str, int]) -> tuple:
    """勤怠テーブルをフォーマットして表示用文字列とデータを返す"""
    table_lines = []
    successful_data = []
    skipped_names = []
    total_amount = 0
    
    for data in attendance_data:
        name = data['name']
        hours = data['hours']
        
        if name in wages:
            wage = wages[name]
            amount = calculate_daily_salary(hours, wage)
            total_amount += amount
            
            table_lines.append(
                f"{name:<12} {hours:<6} {format_currency(wage):<8} {format_currency(amount)}"
            )
            successful_data.append({
                'name': name,
                'hours': hours,
                'wage': wage,
                'amount': amount
            })
        else:
            skipped_names.append(name)
    
    return table_lines, successful_data, skipped_names, total_amount


def create_line_message(successful_data: List[Dict], total_amount: int, sales: int, 
                       with_gross: bool = False) -> str:
    """LINEメッセージを作成"""
    lines = ["【本日の勤怠・給与計算結果】"]
    lines.append("")
    
    # 個別データ
    for data in successful_data:
        lines.append(
            f"{data['name']}: {data['hours']}h × {format_currency(data['wage'])} = {format_currency(data['amount'])}"
        )
    
    lines.append("")
    lines.append(f"給与合計: {format_currency(total_amount)} ({len(successful_data)}名)")
    lines.append(f"売上: {format_currency(sales)}")
    
    if with_gross:
        gross = sales - total_amount
        lines.append(f"粗利: {format_currency(gross)}")
    
    return "\n".join(lines)


def create_incomplete_reminder_message(incomplete_names: List[str]) -> str:
    """未入力リマインドメッセージを作成"""
    if not incomplete_names:
        return ""
    
    lines = ["【未入力リマインド】"]
    lines.append("以下の方の勤怠入力が不完全です:")
    lines.append("")
    
    for name in incomplete_names:
        lines.append(f"・{name}")
    
    lines.append("")
    lines.append("出勤・退勤・休憩時間・勤務時間を確認してください。")
    
    return "\n".join(lines)


def save_log_csv(date_str: str, successful_data: List[Dict], skipped_names: List[str], 
                total_amount: int, sales: int, gross: int, line_success: bool, 
                errors: List[str]):
    """ローカルCSVログを保存"""
    logs_dir = BASE_DIR / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    csv_filename = f"{date_str.replace('/', '')}.csv"
    csv_path = logs_dir / csv_filename
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # ヘッダー
        writer.writerow(['timestamp_jst', 'date', 'name', 'hours', 'wage', 'amount', 
                        'total_amount', 'sales', 'gross', 'line_success', 'errors'])
        
        # データ行
        timestamp = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
        
        if successful_data:
            for data in successful_data:
                writer.writerow([
                    timestamp, date_str, data['name'], data['hours'], data['wage'],
                    data['amount'], total_amount, sales, gross, line_success, 
                    '; '.join(errors) if errors else ''
                ])
        else:
            # データがない場合も1行記録
            writer.writerow([
                timestamp, date_str, '', '', '', '', 0, sales, gross, 
                line_success, '; '.join(errors) if errors else ''
            ])


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='勤怠・時給・売上計算とLINE通知ツール')
    parser.add_argument('--with-gross', action='store_true', help='粗利を計算してLINEに追加')
    parser.add_argument('--dry-run', action='store_true', help='LINE送信せずログのみ出力')
    parser.add_argument('--remind-incomplete', action='store_true', help='未入力リマインドも送信')
    
    args = parser.parse_args()
    
    try:
        # 環境変数読み込み
        load_environment()
        
        # 今日の日付取得
        date_str = get_today_jst()
        print(f"[INFO] Date (JST): {date_str}")
        
        # シート名取得
        sheet_attend = os.getenv('SHEET_ATTEND', '勤怠')
        sheet_wage = os.getenv('SHEET_WAGE', '時給')
        sheet_sales = os.getenv('SHEET_SALES', '売上')
        
        # 勤怠データ取得
        attendance_data = get_attendance(date_str, sheet_attend)
        print(f"[INFO] Target rows: {len(attendance_data)} (checked=TRUE)")
        
        if not attendance_data:
            print("[INFO] 該当なし")
            sys.exit(0)
        
        # 時給データ取得
        wages = get_wages(sheet_wage)
        
        # 売上データ取得
        sales = get_sales(date_str, sheet_sales)
        
        # 勤怠テーブル作成
        table_lines, successful_data, skipped_names, total_amount = format_attendance_table(
            attendance_data, wages
        )
        
        # 粗利計算
        gross = sales - total_amount if args.with_gross else 0
        
        # エラー・警告メッセージ
        errors = []
        if skipped_names:
            for name in skipped_names:
                print(f"[WARN ] Missing wage for '{name}' -> skipped")
            errors.append(f"Missing wages for: {', '.join(skipped_names)}")
        
        print("─" * 50)
        print("Name        Hours  Wage      Amount")
        for line in table_lines:
            print(line)
        print("─" * 50)
        print(f"TOTAL: {format_currency(total_amount)} ({len(successful_data)} people)")
        print(f"SALES: {format_currency(sales)}")
        if args.with_gross:
            print(f"GROSS: {format_currency(gross)}  (with --with-gross)")
        
        # LINE送信
        line_success = False
        if not args.dry_run:
            line_message = create_line_message(successful_data, total_amount, sales, args.with_gross)
            
            token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
            user_id = os.getenv('LINE_TO_USER_ID')
            
            success, error_msg = push_text(user_id, line_message, token)
            
            if success:
                print("[LINE] pushed: OK")
                line_success = True
            else:
                print(f"[ERROR] LINE push failed: {error_msg}")
                errors.append(f"LINE push failed: {error_msg}")
        else:
            print("[LINE] skipped (dry-run)")
        
        # 未入力リマインド
        if args.remind_incomplete:
            incomplete_names = get_incomplete_rows(date_str, sheet_attend)
            if incomplete_names:
                reminder_message = create_incomplete_reminder_message(incomplete_names)
                if not args.dry_run:
                    token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
                    user_id = os.getenv('LINE_TO_USER_ID')
                    
                    success, error_msg = push_text(user_id, reminder_message, token)
                    if not success:
                        print(f"[ERROR] Reminder push failed: {error_msg}")
                        errors.append(f"Reminder push failed: {error_msg}")
                else:
                    print(f"[INFO] Reminder would be sent for: {', '.join(incomplete_names)}")
            else:
                print("[INFO] No incomplete entries found")
        
        # ローカルCSVログ保存
        save_log_csv(date_str, successful_data, skipped_names, total_amount, sales, 
                    gross, line_success, errors)
        print(f"[LOG ] saved: logs/{date_str.replace('/', '')}.csv")
        
        # runlogシートに追加
        if not args.dry_run:
            timestamp_jst = datetime.now(pytz.timezone('Asia/Tokyo')).isoformat()
            runlog_row = {
                'timestamp_jst': timestamp_jst,
                'date': date_str,
                'people': len(successful_data),
                'amount_total': total_amount,
                'sales': sales,
                'gross': gross,
                'success': len(successful_data),
                'skipped': len(skipped_names),
                'errors': '; '.join(errors) if errors else ''
            }
            
            append_runlog(runlog_row)
            print("[SHEET] runlog appended")
        
        # 最終結果サマリー
        if skipped_names:
            print(f"[INFO ] Target rows: {len(attendance_data)} -> Success: {len(successful_data)}, Skipped: {len(skipped_names)}")
        
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(2)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(3)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
