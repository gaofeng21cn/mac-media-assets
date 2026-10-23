# MAC Media Assets 文档索引

这是 `mac-media-assets` 的维护与使用入口。仓库保存公开、可复用的医学科普媒体资产及其精确版本记录；作者专属人物、授权声线、品牌参数和带品牌样片由作者或系列档案保管。

## 使用入口

- [根 README](../README.md)：安装、离线查询、当前库存、许可证和边界。
- [资产清单](asset-inventory.md)：按类别列出当前公共版本及原记录链接。
- [覆盖与储备规划](asset-coverage.md)：角色姿态、组合、成熟度、已知缺口和下一批补充顺序。
- [初稿质量基线](first-draft-quality.md)：写分镜前的查询、实看、代表镜头和当前镜头复核。
- [交互审看入口](interaction-review/README.md)：组合小样、关键帧和回读证据。

## 治理与技术入口

- [资产库治理与 Review 边界](governance-and-review.md)：公共库职责、版本、复用和独立审看层级。
- [catalog 说明](../catalog/README.md)：`catalog/assets.jsonl` 的字段职责和精确版本引用。
- [公共载荷说明](../payloads/README.md)：`payloads/`、来源证据、SHA-256 和离线校验。
- [资产发现](../tools/query_assets.py)：按名称、别名、类别、角色、姿态、组合和叙事用途只读查询。
- [生成素材登记](../tools/ingest_generated.py)：测量 alpha/bounds，拒绝空透明图、烘焙背景和未获允许的光晕。
- [目录校验](../tools/verify_catalog.py)：检查身份、记录、载荷、哈希、组合和覆盖引用。
- [内容锁](../tools/materialize_package.py)：刷新或检查 OPL capability descriptor 的内容锁。

## 验收边界

资产登记、真实 `query → use`、manifest 的 bounds/registration 回读、组合试装、连续动作、完整听感、医学审看和发布资格分别保留证据。文件存在、哈希一致、浏览器脚本通过或一组静态姿态通过，都不会自动升级其他审看层级。

本机当前作者为 Dr.咩 时，泛称“医生”和作者档案明确的女性医生别名走本机作者形象；男性医生和 `generic` 检索走公共通用医生。公共库不含 Dr.咩 私有母版、私有姿态、声线和品牌材料。公共通用医生可在明确选择时取用，并附带身份上下文说明。

## 维护验证

```bash
python3 -m unittest discover -s tests -v
python3 tools/verify_catalog.py
python3 tools/materialize_package.py --check
git diff --check
```

修改目录或载荷后先运行 `python3 tools/materialize_package.py`，再运行上述检查。发布由 OPL Framework 的既有 Package 发布入口负责；本仓库不维护第二套发布器、安装器或 `latest` 指针。
