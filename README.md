# MAC Media Assets · Med Auto Cast 医学科普媒体资产库

`mac-media-assets` 是 [Med Auto Cast（MAC）](https://github.com/gaofeng21cn/med-autocast) 的外挂医学科普媒体资产库，负责统一保管可复用的纸片拼贴、环境板、透明主体、医学纸件、固定件、动作组件、关键帧参考和原创音乐分轨。它与具体系列、作者品牌和单集制作解耦，供内容策划、视觉导演、动画制作和 Review 共同查询。

索引、来源记录和真实载荷都保存在 Git 中。克隆私有仓库后可以直接运行查询与校验，不需要另外从原制作工作台搬素材。具体素材的复用权限仍以来源与作者范围登记为准。

当前由工作台 `/Users/gaofeng/workspace/科普视频` 同步建立，覆盖 11 个系列：科学减重、血脂管理、高血压、糖尿病、垂体瘤、高尿酸与痛风、Graves 病、桥本甲状腺炎、乳腺结节、多囊卵巢综合征、慢性肾病。首版登记包含 48 个纸剧场版本包和 72 张静态关键帧参考。

## 使用

```sh
python3 tools/query_assets.py --query 纸景
python3 tools/query_assets.py --kind transparent_subject --json
python3 tools/query_assets.py --series gout_paper_theatre
python3 tools/query_assets.py --usable-for 透明主体
python3 tools/sync_from_workbench.py --workspace /Users/gaofeng/workspace/科普视频 --root .
python3 tools/verify_catalog.py
```

查询只读；同步是幂等的，会保留已有登记和载荷指纹。新资产先在工作台或本库登记真实文件、来源/许可或生成回执、内容 bounds、透明度、连接点、适用范围、拒用原因和审看边界，再进入推荐集合。

`collections/series.json` 维护系列别名；垂体瘤的 `pituitary_tumor_s01` 与 `pituitary_paper_theatre` 会被查询为同一系列。`verify_catalog.py` 只校验登记、文件存在和 SHA-256，不把机器通过解释成医学或发布通过。

## 资产状态边界

`reference_only` 只能帮助导演找构图和物件关系；`review_candidate` 可以进入候选镜头但仍需当前镜头审看；`approved_direct_use` 也只表示原件在登记范围内可直接取用。静态关键帧不证明连续动作，纸片入库不证明医学含义，配乐分轨入库不证明完整听感。医生形象、授权声线和品牌基线由 MAC 作者/系列档案持有；历史登记中的两项作者范围音乐/图形快照仅供对应作者使用，不进入通用推荐。

库按 `kind`、系列、复用范围和审看边界组织；每次真正使用还要在单集 `asset_manifest.json` 和 `uses.json` 登记。资产库提供稳定下限，导演仍要为每集重新决定故事、比例、接触、遮挡、节奏和声音落点。

- 统一索引：[catalog/assets.jsonl](catalog/assets.jsonl)
- 系列集合：[collections/series.json](collections/series.json)
- 资产合同：[schemas/asset.schema.json](schemas/asset.schema.json)
- 初稿质量与返修经验：[docs/first-draft-quality.md](docs/first-draft-quality.md)
- 资产治理与 Review 边界：[docs/governance-and-review.md](docs/governance-and-review.md)
- 与工作台的同步回执：[catalog/sync-readback.json](catalog/sync-readback.json)
