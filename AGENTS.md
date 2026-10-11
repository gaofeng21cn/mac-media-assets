# MAC Media Assets

这是 Med Auto Cast（MAC）的独立医学科普媒体资产库，技术名为 `mac-media-assets`。

- `catalog/assets.jsonl` 持有可复用资产版本及载荷引用，真实文件位于 `payloads/`，二者一起纳入 Git。
- 可用素材保留原字节、来源和授权、审看范围；不得用静态参考或文件存在声明动态、医学、听感或发布通过。
- 新工作使用配置与相对路径；作者范围资产不作为通用推荐，授权声线和人物母版仍由作者档案管理。
- 机器只校验文件、身份、版本和哈希；素材语义与创作质量由实际 Review 判断，欠项不阻断其他可消费工作。
- 修改后运行 `python3 tools/verify_catalog.py`、实际查询和 `git diff --check`。查询只读；同步仅保留当前可复用版本，按精确版本淘汰不合格与被替代素材。
