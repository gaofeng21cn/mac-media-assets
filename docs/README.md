# MAC Media Assets 文档索引

这是 `mac-media-assets` 的维护与使用入口。仓库保存公开、可复用的医学科普媒体资产及其精确版本记录；作者专属人物、授权声线、品牌参数和带品牌样片由作者或系列档案保管。

## 使用入口

- [根 README](../README.md)：素材预览、分类职责、MAC 接入和独立查询。
- [覆盖与复用范围](asset-coverage.md)：角色姿态、结构解释、组合类别和已知缺口（实时数量以 `tools/query_assets.py` 为准）。
- [生产基线身份](asset-identity-baseline.md)：生产人物身份家族与已识别漂移规则。
- [人物原图标尺](character-scale.md)：原图身体像素/厘米标定、锚点分离与多帧坐标换算。
- [动作样片与取用](motion-studies.md)：人物接触、监测、生活与结构解释的可复用动作包与取用方法。
- [轻量安装与缓存](media-storage.md)：默认目录包、精确媒体取用、压缩完整离线包及两层自动整理流程。
- [医学任务覆盖](../collections/medical-coverage.json)：科普任务的已有候选、缺口与补充优先级。

## 治理与技术入口

- [资产库治理、初稿准备与 Review 边界](governance-and-review.md)：公共库职责、状态与版本复用、初稿准备检查及独立审看层级。
- [比例与接触撤回审计收据](quality-audit-2026-11-01.md)：`collections/` 引用的历史撤回与修复审核依据（配套机读记录见 [quality-audit-2026-11-01.json](quality-audit-2026-11-01.json)）。
- [catalog 说明](../catalog/README.md)：`catalog/assets.jsonl` 的字段职责和精确版本引用。
- [公共载荷说明](../payloads/README.md)：`payloads/`、来源证据、SHA-256 和离线校验。
- [资产发现](../tools/query_assets.py)：按名称、别名、类别、角色、姿态、组合和叙事用途只读查询。
- [生成素材登记](../tools/ingest_generated.py)：测量 alpha/bounds，拒绝空透明图、烘焙背景和未获允许的光晕。
- [目录校验](../tools/verify_catalog.py)：检查身份、记录、载荷、哈希、组合和覆盖引用。
- [内容锁](../tools/materialize_package.py)：刷新或检查 OPL capability descriptor 的内容锁。

## 验收边界

资产登记、真实 `query → use`、manifest 的 bounds/registration 回读、组合试装、连续动作、完整听感、医学审看和发布资格分别保留证据。文件存在、哈希一致、浏览器脚本通过或一组静态姿态通过，都不会自动升级其他审看层级。

工作台作者档案启用 `default_for_clinician` 时，医生性别别名、`generic`、旧公共医生 ID 与自定义医生别名均沿作者私有母版解析；缺姿态沿作者母版补齐。公共通用医生供未启用该策略的工作区取用。作者私有母版、姿态、声线和品牌材料保管在私有工作区。

## 维护验证

开发验证使用 Python 3.11、Pillow 和 Node.js 24。

```bash
uv run --with Pillow python -m unittest discover -s tests -v
node --test tests/medical-processes.test.mjs
python3 tools/repository_media.py audit
python3 tools/apply_curation.py --check
python3 tools/verify_catalog.py --metadata-only
python3 tools/query_assets.py --query 肾脏 --limit 5
node tools/check_motion_studies.mjs
python3 tools/materialize_package.py --check
git diff --check
```

修改目录或载荷后先运行 `python3 tools/materialize_package.py` 刷新 capability descriptor 的内容锁，再运行上述检查。`records/` 中的历史工作台路径仅说明来源；消费者通过 installed descriptor 使用实际安装根目录和目录内相对引用。

发布由 OPL Framework 的既有 `publish-package.yml` 选择准确版本、源码提交和 OCI predecessor 后执行。本仓库不维护第二套发布器、安装器或 `latest` 指针。
