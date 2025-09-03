import pandas as pd
import numpy as np

def analyze_student_scores(csv_file_path):
    """
    CSVファイルから学生のスコアデータを読み込み、統計情報を算出する
    """
    try:
        # ★ 文字化け対策
        df = pd.read_csv(csv_file_path, encoding="utf-8-sig")

        # ★ 必須列の存在チェック
        required_cols = {"名前", "科目", "スコア"}
        missing = required_cols - set(df.columns)
        if missing:
            raise KeyError(f"必要な列が見つかりません: {missing} / 実際の列: {list(df.columns)}")

        # ★ スコアを数値化して欠損は除外（'85点' など混入しても落ちない）
        df["スコア"] = pd.to_numeric(df["スコア"], errors="coerce")
        df = df.dropna(subset=["スコア"])

        print(f"データファイル: {csv_file_path}")
        print(f"読み込まれたデータ数: {len(df)}件")
        print(f"参加者数: {df['名前'].nunique()}名")
        print("---" * 20)

        student_stats = {}
        for student_name in df["名前"].unique():
            student_data = df.loc[df["名前"] == student_name, "スコア"]
            if len(student_data) == 0:
                continue
            stats = {
                "平均点": round(student_data.mean(), 2),
                "最高点": int(student_data.max()),
                "最低点": int(student_data.min()),
                "科目数": int(len(student_data)),
                "合計点": int(student_data.sum()),
            }
            student_stats[student_name] = stats

        return student_stats, df

    except FileNotFoundError:
        print(f"エラー: ファイル '{csv_file_path}' が見つかりません。")
        return None, None
    except Exception as e:
        print(f"エラー: ファイルの読み込み中に問題が発生しました: {e}")
        return None, None

def display_results(student_stats, df):
    if student_stats is None or df is None or df.empty:
        return []

    output_lines = []

    header = "=" * 60
    title = "📊 参加者別スコア統計"
    output_lines.extend([header, title, header])
    print(header); print(title); print(header)

    all_scores = df["スコア"]
    overall_stats = {
        "全体平均": round(all_scores.mean(), 2),
        "全体最高点": int(all_scores.max()),
        "全体最低点": int(all_scores.min()),
        "全体標準偏差": round(all_scores.std(), 2),
    }

    overall_section = ["📈 全体統計",
                       f"  全体平均: {overall_stats['全体平均']}点",
                       f"  全体最高点: {overall_stats['全体最高点']}点",
                       f"  全体最低点: {overall_stats['全体最低点']}点",
                       f"  標準偏差: {overall_stats['全体標準偏差']}点",
                       "---" * 20]
    output_lines.extend(overall_section)
    for line in overall_section[:-1]:
        print(line)
    print("---" * 20)

    participants_section = ["👥 参加者別詳細", "---" * 20]
    output_lines.extend(participants_section)
    print("👥 参加者別詳細"); print("---" * 20)

    sorted_students = sorted(student_stats.items(), key=lambda x: x[1]["平均点"], reverse=True)
    for rank, (student_name, stats) in enumerate(sorted_students, 1):
        student_info = [
            f"🏆 第{rank}位: {student_name}",
            f"   平均点: {stats['平均点']}点",
            f"   最高点: {stats['最高点']}点",
            f"   最低点: {stats['最低点']}点",
            f"   科目数: {stats['科目数']}科目",
            f"   合計点: {stats['合計点']}点",
            "",
        ]
        output_lines.extend(student_info)
        for line in student_info[:-1]:
            print(line)
        print()

    subjects_section = ["📚 科目別統計", "---" * 20]
    output_lines.extend(subjects_section)
    print("📚 科目別統計"); print("---" * 20)

    subject_stats = df.groupby("科目")["スコア"].agg(["mean", "max", "min", "count"]).round(2)
    subject_stats.columns = ["平均点", "最高点", "最低点", "受験者数"]
    for subject, stats in subject_stats.iterrows():
        line = f"  {subject}: 平均{stats['平均点']}点, 最高{int(stats['最高点'])}点, 最低{int(stats['最低点'])}点 ({int(stats['受験者数'])}名)"
        output_lines.append(line)
        print(line)

    return output_lines

def additional_analysis(student_stats, df):
    if student_stats is None or df is None or df.empty:
        return []

    output_lines = []
    header = "=" * 60
    title = "🔍 追加分析"
    output_lines.extend([header, title, header])
    print("\n" + header); print(title); print(header)

    output_lines.append("📊 スコア分布")
    print("📊 スコア分布")

    total = len(df)
    bins = [(0, 60, "60点未満"), (60, 70, "60-69点"),
            (70, 80, "70-79点"), (80, 90, "80-89点"),
            (90, 101, "90-100点")]  # ★ 上端を101にして100を含める

    for lo, hi, label in bins:
        if lo == 0:
            count = (df["スコア"] < hi).sum()
        elif hi == 101:
            count = (df["スコア"] >= lo).sum()
        else:
            count = ((df["スコア"] >= lo) & (df["スコア"] < hi)).sum()
        pct = 0.0 if total == 0 else round(count / total * 100, 1)
        line = f"  {label}: {int(count)}件 ({pct}%)"
        output_lines.append(line)
        print(line)

    output_lines.append("")
    output_lines.append("🏅 優秀者（平均80点以上）")
    print("\n🏅 優秀者（平均80点以上）")

    excellent = [(n, s) for n, s in student_stats.items() if s.get("平均点", 0) >= 80]
    if excellent:
        for name, stats in excellent:
            line = f"  {name}: 平均{stats['平均点']}点"
            output_lines.append(line)
            print(line)
    else:
        output_lines.append("  該当者なし")
        print("  該当者なし")

    return output_lines

def save_to_file(lines, filename="analysis_result.txt"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")
        print(f"\n📁 分析結果を {filename} に保存しました。")
    except Exception as e:
        print(f"エラー: ファイルの保存中に問題が発生しました: {e}")

def main():
    print("🎯 CSVデータ分析プログラム")
    print("=" * 50)

    csv_file = "課題2.csv"  # ← ここはフォルダ内の実ファイル名に合わせる
    print(f"CSVファイル: {csv_file}")

    print("データ分析を開始します...")
    student_stats, df = analyze_student_scores(csv_file)
    print("データ分析が完了しました。")

    if student_stats:
        print("結果を表示します...")
        main_out = display_results(student_stats, df)

        print("追加分析を実行します...")
        add_out = additional_analysis(student_stats, df)

        completion = ["", "=" * 60, "✅ 分析完了"]
        print("\n" + "=" * 60); print("✅ 分析完了")

        all_out = (main_out or []) + (add_out or []) + completion
        print("結果をファイルに保存します...")
        save_to_file(all_out)
    else:
        print("データの分析に失敗しました。")

if __name__ == "__main__":
    print("プログラムを開始します...")
    main()
    print("プログラムが終了しました。")
