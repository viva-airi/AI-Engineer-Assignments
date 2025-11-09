"""
在庫状況のマッピング定義
"""

# 在庫状況のマッピング辞書
# 未該当の場合は "unknown" として扱う
AVAILABILITY_MAP = {
    "在庫あり": "in_stock",
    "在庫切れ": "out_of_stock"
}
