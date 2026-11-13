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
项目导入仍复制独立文件，项目清单和审看范围沿用原合同。修改项目文件不会污染共享缓存，删除缓存也不影响已导入的项目。

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

源码与历史归档保留既有原始字节；本次完整安装导出采用下述压缩版本和内容去重。若源仓库媒体继续增长，可将大对象迁到现有 OCI/对象存储并保持同一 SHA-256 索引；迁移前验证来源、恢复和授权，保留完整历史镜像。

## 完整离线包的媒体压缩

完整版默认也去重。同一 SHA-256 的媒体在安装目录只占一份数据，组件的多个相对路径通过硬链接引用它；归档保留硬链接，安装时重新核对哈希并建立链接。目录大小与软件中心显示以实际唯一内容为主，所有引用路径的累计字节只作辅助统计。项目导入仍复制独立文件，不把项目修改与共享库连接在一起。

安装目录直接使用 WebP、AAC/M4A 和 FLAC，不再展开回 PNG/WAV。图片默认 WebP Q90，原尺寸、Alpha 和可迁移颜色元数据保留；矢量派生的医学线图使用无损 WebP，16位或动画PNG保留原格式。音乐仅在 AAC 192kbps 比 FLAC 还节省至少15%时选AAC；短拟音、节拍和旋律分轨保留FLAC。已经有效压缩的JPEG/MP4不重复转码。

压缩包内的资产生成独立 revision、文件扩展名和SHA-256，并同步组合、代码、预览及人物标尺的引用。`delivery.source_asset_id` 指回源码原版本，`catalog/delivery-report.json` 保存原ID到压缩版本的映射。现有工程不会被自动改写；新取用识别已安装的压缩库，复制压缩字节。来源撤回继续生效，有损版本不继承原件的视觉和听感通过结论。

```sh
# 构建机需要 cwebp、flac、ffmpeg；Pillow只用于更快的像素校验，可省略。
python3 tools/optimize_media.py --export /库外/mac-media-assets --archive /库外/mac-media-assets-offline.tar.gz
# 离线机器只需既有Python；从完整归档安装，不运行编码器或联网。
python3 tools/offline_installation.py --operation install --source-root /库外/mac-media-assets-offline.tar.gz
```

同一owner的软件中心动作可从 `MAC_MEDIA_OFFLINE_SOURCE` 指定的预构建目录/归档安装；未指定时仍支持从固定源码构建，编码器缺失会在下载前说明缺项。正式分发需由现有 Framework OCI 流程发布该预构建完整资料，不能把本地归档当成已发布的软件中心制品。轻量核心与完整媒体仍使用同一Package，Full App继续只携带轻量核心。

独立角色、器官和可拼接部件必须有真实透明区域；完整后景允许不透明。`tools/audit_transparency.py` 按登记用途审计入口和动作图层，压缩构建会拒绝完全不透明的独立运动层，并逐图核对Alpha。全透明像素的RGB并非背景色块，假棋盘、边缘白边或已烘焙场景仍需浅/深/彩底和当前舞台审看。Dr.咩等作者私有图册由其工作区维护，本公共库不收录或覆盖。
