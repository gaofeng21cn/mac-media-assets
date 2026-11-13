#!/usr/bin/env python3
"""Rebuild a browse index from current exact candidates; counts do not approve quality."""
import json
from pathlib import Path
from query_assets import query

ROOT=Path(__file__).resolve().parents[1]


def build(root=ROOT):
    rows=query(root)
    categories=json.loads((root/'collections/taxonomy.json').read_text())['categories']
    lines=['# 当前素材清单','','按默认查询列出当前公共候选，历史和撤回版本不重复计数。原件、来源、许可和审核范围见精确原记录。',
           '',f'当前共有 {len(rows)} 项、{len(categories)} 类。轻量安装保留全部原记录，媒体实际到位情况以查询的 storage 为准。',
           '', '[医学任务覆盖与缺口](../collections/medical-coverage.json) · [按需获取与离线使用](media-storage.md) · [医学过程动态组件](../tools/preview-engine/processes.html)']
    for category in categories:
        current=[r for r in rows if r['discovery'].get('category')==category['id']]
        lines+=['',f"## {category['label']}（{len(current)}）",'', '| 素材 | 精确原记录 |','| --- | --- |']
        for row in current:
            lines.append(f"| {row['display_title']} | [原记录](../{row['portable_record']}) |")
    result='\n'.join(lines)+'\n'
    (root/'docs/asset-inventory.md').write_text(result)
    return {'assets':len(rows),'categories':len(categories)}


if __name__=='__main__':print(json.dumps(build(),ensure_ascii=False))
