#!/usr/bin/env python3
"""
学术论文引用规范化工具。

用途：把从知网(CNKI)/万方/维普等平台人工摘录的题录信息，
规范化为统一引用格式，并按期刊级别自动标注可信度权重，
便于Phase 2提炼时按来源优先级排序取用。

本脚本不做任何自动抓取——知网等平台的全文与题录检索
通常需要订阅账号或有严格的反爬限制，所有题录信息应由
人工在页面上核实摘录后，整理为输入的JSON文件。

输入文件格式示例（entries.json）：
[
  {
    "author": "张三",
    "author_order": "第一作者",
    "title": "论指导性案例的参照效力",
    "journal": "法律适用",
    "year": "2022",
    "issue": "3",
    "pages": "45-53",
    "source_note": "知网题录页手动核实，2026-07-09"
  }
]

用法：
    python3 cnki_citation_formatter.py entries.json
    python3 cnki_citation_formatter.py entries.json --md   # 输出markdown表格
"""
import json
import sys
from pathlib import Path

# 法院系统权威业务期刊——最高权重
CORE_JOURNALS_TIER1 = {"法律适用", "人民司法", "数字法治"}

# 常见CLSCI核心法学期刊——高权重（按实际检索结果核实增补，非穷尽列表）
CLSCI_JOURNALS = {
    "中国法学", "法学研究", "法学", "法商研究", "法学家",
    "现代法学", "法律科学", "比较法研究", "环球法律评论",
    "清华法学", "中外法学", "中国刑事法杂志", "法制与社会发展",
    "政法论坛", "法学评论", "行政法学研究", "知识产权",
}


def classify(journal_name: str) -> str:
    if journal_name in CORE_JOURNALS_TIER1:
        return "最高权重·法院系统权威业务期刊"
    if journal_name in CLSCI_JOURNALS:
        return "高权重·CLSCI核心法学期刊"
    return "需人工核实期刊级别"


def author_weight_note(author_order: str) -> str:
    if not author_order:
        return "署名顺序未知，需核实是否代表该法官本人主导观点"
    if "第一作者" in author_order or "独著" in author_order or "通讯作者" in author_order:
        return "主导作者，可较高权重采纳"
    return "非主导作者（合著），采纳时需降低权重，注明为参与观点"


def format_entry_text(e: dict) -> str:
    tier = classify(e.get("journal", ""))
    weight_note = author_weight_note(e.get("author_order", ""))
    return (
        f"{e.get('author', '未知')}. {e.get('title', '（无标题）')}[J]. "
        f"{e.get('journal', '未知期刊')}, {e.get('year', '未知年份')}"
        f"({e.get('issue', '?')}): {e.get('pages', 'N/A')}. "
        f"[{tier}] [{weight_note}]"
    )


def format_entry_md_row(e: dict) -> str:
    tier = classify(e.get("journal", ""))
    weight_note = author_weight_note(e.get("author_order", ""))
    return (
        f"| {e.get('author','')} | {e.get('title','')} | {e.get('journal','')} "
        f"| {e.get('year','')}({e.get('issue','')}) | {tier} | {weight_note} |"
    )


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    path = Path(sys.argv[1])
    as_md = "--md" in sys.argv

    with path.open(encoding="utf-8") as f:
        entries = json.load(f)

    if as_md:
        print("| 作者 | 标题 | 期刊 | 年期 | 可信度 | 署名权重提示 |")
        print("|------|------|------|------|--------|--------------|")
        for e in entries:
            print(format_entry_md_row(e))
    else:
        for e in entries:
            print(format_entry_text(e))


if __name__ == "__main__":
    main()
