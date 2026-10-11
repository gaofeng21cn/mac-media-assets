---
name: mac-media-assets
description: 检索和审看 Med Auto Cast 独立媒体库中的纸片、纸景、代码动作与声音，选择适合当前故事的复用起点，并保存新创材料与使用边界。
---

# MAC 媒体资产

本库是 MAC 的独立能力与媒体仓库，根目录在本 Skill 上两级。查询工具是 `../../tools/query_assets.py`，真实文件引用相对于仓库根。从 MAC 调用时，优先使用 MAC 的 `media_asset_library` 工具，按工作区配置发现本库并把选中版本复制到当前项目。

导演准备先按患者问题、视觉锚点和拟承担动作检索，再实际查看原件和动作样例。环境板、透明主体、纸材固定件、静态参考、组件和声音各有职责；按内容 bounds、认知关系和当前构图决定比例。库里已有的故事、构图、镜头时码和颜色不成为新集模板。

```sh
python3 tools/query_assets.py --query 垂体 --json
python3 tools/query_assets.py --kind code_component --json
python3 tools/query_assets.py --kind audio --author-id <当前作者档案ID> --json
```

默认检索不推荐其他作者的品牌资产。`--include-author-assets` 仅供策展发现，不授予使用权；专用声线、医生形象和系列品牌仍由 MAC 作者档案管理。

看过候选后，按本集用途选择原件复用、局部适配、另找合法素材或 ImageGen 新创。无需满足复用数量、复用率或固定镜头数。没有合适素材或库不可用时记录诊断，继续故事与新创；不能为了复用把不合适纸件塞进画面。复用技法提供下限，代表镜头和整集的连续审片推动上限。

`reference_only` 静帧只供参考，不能冒充可运动的透明纸件。实际取用保留精确 ID、版本、来源与许可、真实文件及原审核范围；当前镜头的视觉、医学和听感重新审查。文件、哈希和入库不签发任何质量或发布批准。

交付后的精选新创可从工作台同步：`python3 tools/sync_from_workbench.py --workspace <目录> --root <本库>`。保存独立载荷、原记录与证据、适用/失败条件，保留旧版本；先执行 `tools/verify_catalog.py`，再由模型审看复用价值。同步和推送属于明确写操作，查询不隐式更新库。
