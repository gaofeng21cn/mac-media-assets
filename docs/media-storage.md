# 轻量安装、按需媒体与缓存

标准 OPL 安装仍使用 `opl packages install med-autocast --json`，MAC 依赖本能力包。
本次源码将默认内容锁改为轻量目录：工具、分类、全量精确版本记录和体积小的原创医学代码组件随包；原始图像、声音和历史样片按需获取。
此文描述本次源码行为；已发布 0.2.1 的载荷不会因此改变，下一次发布须按 Framework 原流程更新投影与载荷清单。

## 三种使用方式

| 方式 | 本地内容 | 适用情况 |
| --- | --- | --- |
| 默认目录包 | 全量索引、来源和审核记录、工具、轻量代码组件 | 日常按主题选择素材 |
| 按主题预取 | 目录包加选中分类、查询或精确版本的媒体缓存 | 外出、离线制作、固定系列 |
| 离线完整版 | 全部登记媒体、全量索引、来源与审核记录、工具 | 无网制作与完整离线使用 |

所有 MAC 标准安装入口默认依赖轻量目录包；OPL App Full 也集成这份小核心。软件中心在同一素材库详情中提供“安装离线完整版”，先准备轻量核心，再由本库 owner 安装完整媒体。它沿用同一个 Package identity，不另建产品条目。此入口需随 Framework、Studio 和素材新版一并交付，已发布旧版本的行为不变。

离线版安装于共享缓存根的 `offline/versions/<版本指纹>`，以原子指针切换；该目录独立于可清理的按需缓存。逐项核对全部登记媒体的长度与 SHA-256 后才生效，更新失败保留原安装。软件中心按安装修订号卸载离线资料，保留轻量核心、源码和制作项目。

维护者也可以生成可搬运的完整目录包：`python3 tools/materialize_package.py --profile full --export <库外新目录>`。目录携带独立完整内容锁，可整目录搬到离线机器，再沿 MAC 的 `asset_library.root` 接入；不要求离线机器另行下载。完整源码克隆仍供维护与历史归档使用。

`query` 和 `plan` 只读、不访问网络、不隐式写缓存。取用使用精确资产 ID；MAC 的 `use` 在需要时调用本库 `fetch`，完成字节与 SHA-256 校验，再沿原有归档与项目复制链导入。

```sh
python3 tools/query_assets.py --system 呼吸 --patient-task 理解身体功能
python3 tools/media_store.py plan --id reserve_mri_v1
python3 tools/media_store.py fetch --category anatomy --pin
python3 tools/media_store.py fetch --query 糖尿病 --pin
python3 tools/media_store.py fetch --id 'paper:<source_id>@<revision>' --offline
```

计划中的 `download_bytes` 按缺失内容哈希去重；`logical_bytes` 是各条目逻辑大小。
`fetch` 必须指定素材、分类或查询条件，不默认拉取全库。精确撤回决定在获取与 MAC 导入前重新读取，缓存命中不绕过撤回。

## 工作区配置

沿用 `workbench.yaml.asset_library`，不另建安装配置系统。已有 `root` 与作者档案保持原样。新初始化的工作区默认配置：

```yaml
asset_library:
  mode: catalog_with_on_demand_media
  root: ../mac-media-assets
  auto_install: true
  auto_fetch: true
  offline: false
  cache_limit_bytes: 2147483648
  # cache_root: /本机共享媒体缓存
```

`cache_root` 可自定；省略时使用 `MAC_MEDIA_CACHE` 或 `~/.cache/mac-media-assets`。
`offline: true` 或 `auto_fetch: false` 只使用现有媒体与缓存，缺失时返回明确欠项。可用 `--source-root <完整库>` 从本地完整镜像预取，避免联网。
旧版库没有按需获取工具时，MAC 继续支持已有完整媒体；不会把文件缺失误报为取用成功。

## 字节、版本与清理

媒体下载固定到 `catalog/media-storage.json` 的完整 Git 提交，逐文件核对已登记长度和 SHA-256；不用漂移的 `main` 作为媒体字节来源。
相同哈希在共享 `blobs/` 中只存一份，原始记录与版本不改写。HTML 预览通过可丢弃的 `snapshots/` 关系视图访问这些文件。
项目导入仍复制独立原件，项目清单和原审核范围保持原合同。修改项目文件不会污染共享缓存，删除缓存也不影响已导入的项目。

```sh
python3 tools/media_store.py cache-status
python3 tools/media_store.py cache-prune --target-bytes 536870912
python3 tools/media_store.py cache-prune --target-bytes 536870912 --apply
```

清理默认只给计划；显式 `--apply` 才删除未固定快照和无引用 blob。`--pin` 的离线快照受保护。预算不足时报告所需空间，不自动删除母版或项目。

## 构建与验收

```sh
python3 tools/materialize_package.py
python3 tools/materialize_package.py --check --export /库外/尚不存在的目录
python3 tools/verify_catalog.py --root /轻量目录 --metadata-only
python3 tools/verify_catalog.py
python3 tools/media_store.py audit
```

默认内容锁仅收录实际要安装的文件，避免在 `records/**/files` 与 `payloads/` 双重携带原图。
`--metadata-only` 明确列出未获取媒体数，只验证本地字节与登记关系；完整库验证仍逐项检查全部原始媒体。
默认核心包有体积预算检查；大文件新增时先决定随包、预取或远端媒体职责，再更新内容锁。`--profile full --export` 在独立导出目录生成完整内容锁，源码始终保留默认轻量锁。

后续发布沿用 OPL Framework 的 descriptor、allowlist 和 OCI 流程，更新其源包投影及内容锁。`--export` 仅提供可检查的目录，不签发版本、不推送 OCI、不改 Stable 指针，也不替代 Framework 安装。

## 工程依据与后续边界

- [Hugging Face 缓存](https://huggingface.co/docs/huggingface_hub/guides/manage-cache)：复用不可变 blob，以版本视图保留文件关系；借鉴共享缓存模式，不增加 Hub 账户或 SDK 依赖。
- [Hugging Face 选择性下载](https://huggingface.co/docs/huggingface_hub/guides/download)：按文件或条件预取，避免默认下载所有媒体。
- [DVC 远端存储](https://doc.dvc.org/user-guide/data-management/remote-storage)：代码/登记与大型数据生命周期分开，完整历史可在远端保留。
- [Git 部分克隆](https://git-scm.com/docs/git-clone)和[稀疏检出](https://git-scm.com/docs/git-sparse-checkout)：MAC 独立获取库时优先下载元数据并检出所需路径，已有库不隐式重置或更新。

本轮首先缩小实际安装和增量取用，不重写 Git 历史，也不转码既有原始字节。若源仓库媒体继续增长，下一步将大对象迁到现有 OCI/对象存储并保持同一 SHA-256 索引；迁移前先验证来源、恢复和授权，保留完整历史镜像。
PNG 无损重压缩、WAV→FLAC 可以作为后续传输表示，解码后须还原登记字节或形成明确新版本；不以有损转码或删除审核证据换取体积数字。
