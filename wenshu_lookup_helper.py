#!/usr/bin/env python3
"""
裁判文书网检索助手：生成标准检索式 + 规范化记录格式，不做自动抓取。

设计原则：本脚本不尝试绕过验证码、不做自动化登录或高频抓取，
只负责(1)生成便于人工/WebSearch工具核实的检索式，
(2)把人工核实后的结果规范化为统一的JSON记录，供后续Phase 2提炼使用。

用法：
    python3 wenshu_lookup_helper.py query "法官姓名" "法院全称" [关键词]
    python3 wenshu_lookup_helper.py record  # 交互式录入一条已核实的文书记录（旧版单条模式）

    本地手动下载文书批量管理（配合 sources/judgments/ 目录结构使用）：
    python3 wenshu_lookup_helper.py scan <skill目录>
        扫描 sources/judgments/raw/ 下的新文件，逐个交互式询问元数据，写入manifest.json

    python3 wenshu_lookup_helper.py sort <skill目录>
        根据manifest.json的校验结果，把raw/下的文件分流到verified/或excluded/

    python3 wenshu_lookup_helper.py list-verified <skill目录>
        列出当前manifest中所有已通过校验、可供Agent 2读取的文书清单
"""
import sys
import json
import shutil
import datetime
from pathlib import Path


def build_queries(judge_name: str, court_name: str, keyword: str = None):
    base = f'"{judge_name}" "{court_name}"'
    queries = [
        f'{base} 裁判文书网',
        f'{base} 承办法官',
        f'{base} 审判长',
        f'site:wenshu.court.gov.cn {judge_name} {court_name}',
    ]
    if keyword:
        queries.append(f'{base} {keyword}')
    return queries


def make_record(judge_name, source_url, doc_number, role_in_case,
                 is_final_effective, verified_by_human, notes=""):
    return {
        "judge_name": judge_name,
        "source_url": source_url,
        "doc_number": doc_number,            # 如 (2021)京01民终XXX号
        "role_in_case": role_in_case,        # 审判长/承办法官/合议庭成员
        "is_final_effective": is_final_effective,   # True/False，未生效一律不采纳
        "verified_by_human": verified_by_human,     # 必须人工核实为True才可采纳
        "notes": notes,
        "recorded_at": datetime.date.today().isoformat(),
    }


def append_record(skill_dir: str, record: dict):
    out_path = Path(skill_dir) / "references" / "research" / "wenshu-records.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"已追加记录到 {out_path}")


def judgments_dir(skill_dir: str) -> Path:
    return Path(skill_dir) / "references" / "sources" / "judgments"


def load_manifest(skill_dir: str) -> dict:
    path = judgments_dir(skill_dir) / "manifest.json"
    if not path.exists():
        return {"records": [], "excluded": []}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_manifest(skill_dir: str, manifest: dict):
    path = judgments_dir(skill_dir) / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"manifest已保存到 {path}")


def known_filenames(manifest: dict) -> set:
    names = {r["filename"] for r in manifest.get("records", [])}
    names |= {r["filename"] for r in manifest.get("excluded", [])}
    return names


def cmd_scan(skill_dir: str):
    """扫描 raw/ 下尚未登记的文件，逐个交互式询问元数据"""
    raw_dir = judgments_dir(skill_dir) / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(skill_dir)
    known = known_filenames(manifest)

    new_files = [p for p in raw_dir.iterdir() if p.is_file() and p.name not in known]
    if not new_files:
        print("没有发现尚未登记的新文件。")
        return

    print(f"发现 {len(new_files)} 个尚未登记的文件，开始逐个录入（Ctrl+C 中途退出，已录入的会保留）：\n")

    for p in new_files:
        print(f"--- 文件: {p.name} ---")
        doc_number = input("案号（如 (2021)京01民终XXX号，直接回车用文件名）: ").strip() or p.stem
        court = input("法院全称: ").strip()
        judge_name = input("法官姓名: ").strip()
        role_in_case = input("该法官在本案中的角色（审判长/承办法官/合议庭成员-非主审）: ").strip()
        case_type = input("案件类型（如 民事二审/刑事一审 等）: ").strip()
        year = input("年份: ").strip()
        is_final = input("是否已生效？(y/n): ").strip().lower() == "y"
        sensitive_ok = input("是否已核对无未成年人/隐私/涉密等不宜公开内容？(y/n): ").strip().lower() == "y"
        verified = input("是否确认核实以上信息属实？(y/n): ").strip().lower() == "y"
        notes = input("备注（可留空）: ").strip()

        record = {
            "filename": p.name,
            "doc_number": doc_number,
            "court": court,
            "judge_name": judge_name,
            "role_in_case": role_in_case,
            "case_type": case_type,
            "year": int(year) if year.isdigit() else year,
            "is_final_effective": is_final,
            "verified_by_human": verified,
            "verified_by": "本人手动核实" if verified else "",
            "verified_at": datetime.date.today().isoformat() if verified else "",
            "sensitive_content_check": "已核对，无敏感内容" if sensitive_ok else "未核对或存在敏感内容，需人工复查",
            "notes": notes,
        }

        if is_final and verified and sensitive_ok:
            manifest.setdefault("records", []).append(record)
            print(f"✅ {p.name} 已登记为可采纳文书\n")
        else:
            reason_parts = []
            if not is_final:
                reason_parts.append("未生效")
            if not verified:
                reason_parts.append("未通过人工核实")
            if not sensitive_ok:
                reason_parts.append("敏感内容未核对或存在敏感内容")
            manifest.setdefault("excluded", []).append({
                "filename": p.name,
                "doc_number": doc_number,
                "reason": "、".join(reason_parts),
                "excluded_at": datetime.date.today().isoformat(),
            })
            print(f"❌ {p.name} 已记录为排除项：{'、'.join(reason_parts)}\n")

    save_manifest(skill_dir, manifest)


def cmd_sort(skill_dir: str):
    """根据manifest把raw/下的文件分流到verified/或excluded/"""
    raw_dir = judgments_dir(skill_dir) / "raw"
    verified_dir = judgments_dir(skill_dir) / "verified"
    excluded_dir = judgments_dir(skill_dir) / "excluded"
    verified_dir.mkdir(parents=True, exist_ok=True)
    excluded_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(skill_dir)
    moved_v, moved_e = 0, 0

    for r in manifest.get("records", []):
        src = raw_dir / r["filename"]
        if src.exists():
            shutil.move(str(src), str(verified_dir / r["filename"]))
            moved_v += 1

    excluded_log = []
    for r in manifest.get("excluded", []):
        src = raw_dir / r["filename"]
        if src.exists():
            shutil.move(str(src), str(excluded_dir / r["filename"]))
            moved_e += 1
        excluded_log.append(r)

    if excluded_log:
        log_path = excluded_dir / "excluded-log.json"
        with log_path.open("w", encoding="utf-8") as f:
            json.dump(excluded_log, f, ensure_ascii=False, indent=2)

    print(f"已移动 {moved_v} 个文件到 verified/，{moved_e} 个文件到 excluded/")


def cmd_list_verified(skill_dir: str):
    """列出manifest中所有已通过校验、可供Agent 2读取的文书"""
    manifest = load_manifest(skill_dir)
    records = manifest.get("records", [])
    if not records:
        print("目前没有已通过校验的文书记录。")
        return
    print(f"共 {len(records)} 份已通过校验的文书，Agent 2可读取分析：\n")
    for r in records:
        weight = "★主审，权重较高" if "主审" in r.get("role_in_case", "") or "审判长" in r.get("role_in_case", "") or "承办" in r.get("role_in_case", "") else "☆非主审，权重较低仅作参考"
        print(f"  - {r['doc_number']} | {r['court']} | {r['role_in_case']} ({weight}) | {r['case_type']} {r['year']}")
        print(f"    文件: verified/{r['filename']}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "query":
        if len(sys.argv) < 4:
            print('用法: python3 wenshu_lookup_helper.py query "法官姓名" "法院全称" [关键词]')
            sys.exit(1)
        judge, court = sys.argv[2], sys.argv[3]
        kw = sys.argv[4] if len(sys.argv) > 4 else None
        print("生成的检索式（请用WebSearch/web_fetch工具逐条核实结果，"
              "确认承办法官身份与文书生效状态后再录入）：\n")
        for q in build_queries(judge, court, kw):
            print(f"  - {q}")
        print("\n⚠️ 未经人工核实的检索结果不得直接写入调研文件。")

    elif mode == "record":
        print("交互式录入一条已核实的裁判文书记录（Ctrl+C 取消）")
        judge_name = input("法官姓名: ").strip()
        source_url = input("文书来源URL（裁判文书网/北大法宝/威科先行）: ").strip()
        doc_number = input("案号（如 (2021)京01民终XXX号）: ").strip()
        role_in_case = input("该法官在本案中的角色（审判长/承办法官/合议庭成员）: ").strip()
        is_final = input("是否已生效？(y/n): ").strip().lower() == "y"
        verified = input("是否已人工核实身份与生效状态？(y/n): ").strip().lower() == "y"
        notes = input("备注（如涉及脱敏/不公开事项说明，可留空）: ").strip()

        if not verified:
            print("⚠️ 未通过人工核实的记录不予保存，请先核实后再录入。")
            sys.exit(1)
        if not is_final:
            print("⚠️ 未生效文书不予采纳，不予保存。")
            sys.exit(1)

        record = make_record(judge_name, source_url, doc_number, role_in_case,
                              is_final, verified, notes)
        skill_dir = input("Skill目录路径（如 .claude/skills/张三-judicial-perspective）: ").strip()
        append_record(skill_dir, record)

    elif mode == "scan":
        if len(sys.argv) < 3:
            print("用法: python3 wenshu_lookup_helper.py scan <skill目录>")
            sys.exit(1)
        cmd_scan(sys.argv[2])

    elif mode == "sort":
        if len(sys.argv) < 3:
            print("用法: python3 wenshu_lookup_helper.py sort <skill目录>")
            sys.exit(1)
        cmd_sort(sys.argv[2])

    elif mode == "list-verified":
        if len(sys.argv) < 3:
            print("用法: python3 wenshu_lookup_helper.py list-verified <skill目录>")
            sys.exit(1)
        cmd_list_verified(sys.argv[2])

    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
