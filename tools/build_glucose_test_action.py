#!/usr/bin/env python3
"""Register the glucose meter operation as a reusable motion recipe.

The library carried the meter, the strip, the bare hand and the dressing as
separate cut outs but no action that uses them together, so an episode could
show a reading but never the insert, the prick, the reading and the press.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import motion_package

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'work' / 'action-contact-repair-20261024' / 'mac_glucose_test_action_v1'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(ROOT))
    parser.add_argument('--stage', default=str(STAGE))
    args = parser.parse_args()
    folder = Path(args.stage)
    sequence = json.loads((folder / 'sequence.json').read_text())
    discovery = {
        'category': 'motion',
        'aliases': [sequence['title'], '血糖仪', '试纸', '采血', '指尖采血', '家庭监测', 'mac_glucose_test_action_v1'],
        'actions': ['器械操作', '试纸插入', '指尖采血', '读数', '按压止血'],
        'medium': 'code',
        'story_roles': ['家庭监测', '糖尿病管理', '连续动作'],
        'display_title': sequence['title'],
        'renderers': ['canvas2d'],
        'sample_duration_seconds': sequence['duration'],
    }
    motion_package.freeze(
        folder, args.root,
        id=sequence['id'], title=sequence['title'], scope=sequence['scope'],
        tags=['paper_collage', 'continuous_action', 'monitoring', 'glucose_test'],
        discovery=discovery,
        source_assets={
            'generation': [],
            'library': sequence['source_assets'],
            'note': '手、血糖仪和敷料复用原字节；试纸重绘为正确长宽比的可编辑 SVG，采血笔为原创代码图形。'
                    '主机端口、试纸两端、指端和敷料共用原图像素接触点。',
        },
        checked=[
            '逐帧核对装入试纸、采血笔接触、试纸保持连接吸血、读取、按压；采样端与同一指端重合。',
            '浅底、深底与彩底三张底图下边缘干净，无光晕与背景残留。',
            '手机宽度核对主机、短试纸、采样接触与敷料；数值读数改为无诊断含义的读取完成提示。',
            '随机拖动时间轴返回完全相同的画面，浏览器无报错。',
        ],
        defects_found_and_fixed=[
            '旧版试纸按宽度缩放后长过主机：重绘短试纸，按两个端点的实际距离等比缩放。',
            '旧版错误演示取出沾血后再插回：改为插好后不再分离，主机和试纸共同靠近血滴。',
            '旧版血滴漂浮与敷料偏移：所有接触均绑定同一个原图指端；补可见采血笔接触。',
        ],
        not_reviewed=[
            '独立医学终审 pending；采血笔与试纸为通用示意，具体设备按说明操作。',
            '本集镜头未审：接触、尺度、遮挡与构图仍需按当前镜头判断。',
            '声音未审：配套拟音已在库，但本包样片无声。',
        ],
        usage_note='导入后位于 `src/library/<id>/<revision>/`，`sequence.json` 记录每层的边界与事件时点，'
                   '`runtime.mjs` 的 `renderStudy(ctx, images, recipe, seconds)` 可直接接进本集 Canvas，时间由本集提供。'
                   '手、血糖仪、试纸与敷料都是独立部件，改比例或落点时重新试装。',
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
