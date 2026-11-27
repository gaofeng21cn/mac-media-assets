# 轻量安装、按需媒体与缓存

标准 OPL 安装使用 `opl pack install med-autocast --json`，MAC 依赖本能力包。
默认内容锁采用轻量目录：工具、分类、全量精确版本记录和体积小的原创医学代码组件随包；已处理图像、声音和样片按需获取，原始母版留在仓库外。

## 三种使用方式

| 方式 | 本地内容 | 适用情况 |
| --- | --- | --- |
| 默认目录包 | 全量索引、来源和审核记录、工具、轻量代码组件 | 日常按主题选择素材 |
| 按主题预取 | 目录包加选中分类、查询或精确版本的媒体缓存 | 外出、离线制作、固定系列 |
| 离线完整版 | 全部登记媒体、全量索引、来源与审核记录、工具 | 无网制作与完整离线使用 |

所有 MAC 标准安装入口默认依赖轻量目录包；OPL App Full 也集成这份小核心。软件中心在同一素材库详情中提供“安装离线完整版”，先准备轻量核心，再由本库 owner 安装完整媒体。它沿用同一个 Package identity，不另建产品条目。此入口由 Framework、Studio 与本库版本合同协同交付。

离线版安装于共享缓存根的 `offline/versions/<版本指纹>`，以原子指针切换；该目录独立于可清理的按需缓存。逐项核对全部登记媒体的长度与 SHA-256 后才生效，更新失败保留原安装。软件中心按安装修订号卸载离线资料，保留轻量核心、源码和制作项目。

维护者也可以生成可搬运的完整目录包：`python3 tools/materialize_package.py --profile full --export <库外新目录>`。目录携带独立完整内容锁，可整目录搬到离线机器，再沿 MAC 的 `asset_library.root` 接入；不要求离线机器另行下载。完整源码克隆仍供维护与历史归档使用。

`query` 和 `plan` 只读、不访问网络、不隐式写缓存。取用使用精确资产 ID；MAC 的 `use` 调用本库 `prepare_media.py`，需要时先 `fetch` 原件，再复用或生成无损使用版，沿原有归档与项目复制链导入。完整包使用同一处理函数和缓存；同一原件产生相同的使用版 revision、字节与引用。

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

历史媒体沿 `catalog/media-storage.json` 的固定Git提交读取；新增处理对象沿固定OCI manifest及SHA-256读取。逐文件核对长度和SHA-256，不使用漂移的main或latest标签确定媒体字节。
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
默认核心包只保留代码、元数据与明确随包的小组件；新增媒体在日常prepare中自动整理到持久对象库并生成压缩视图。`--profile full --export` 在独立导出目录生成完整内容锁，源码始终保留默认轻量锁。

后续发布沿用 OPL Framework 的 descriptor、allowlist 和 OCI 流程，更新其源包投影及内容锁。`--export` 仅提供可检查的目录，不签发版本、不推送 OCI、不改 Stable 指针，也不替代 Framework 安装。

## 工程依据与后续边界

- [Hugging Face 缓存](https://huggingface.co/docs/huggingface_hub/guides/manage-cache)：复用不可变 blob，以版本视图保留文件关系；借鉴共享缓存模式，不增加 Hub 账户或 SDK 依赖。
- [Hugging Face 选择性下载](https://huggingface.co/docs/huggingface_hub/guides/download)：按文件或条件预取，避免默认下载所有媒体。
- [DVC 远端存储](https://doc.dvc.org/user-guide/data-management/remote-storage)：代码/登记与大型数据生命周期分开，完整历史可在远端保留。
- [Git 部分克隆](https://git-scm.com/docs/git-clone)和[稀疏检出](https://git-scm.com/docs/git-sparse-checkout)：MAC 独立获取库时优先下载元数据并检出所需路径，已有库不隐式重置或更新。

原始字节独立保全；新增素材登记、工作台同步、MAC取用和完整安装导出共用无损版本和内容去重。源码、压缩视图与母版的职责按下面两层流程统一处理。

## 源头与每日检查的两层自动整理

素材创建Agent首先遵循仓库根 `AGENTS.md`：图像优先保存无损WebP，整数PCM声音优先FLAC，保留真实来源、稳定身份、用途、bounds和需要的锚点。标准入库和工作台底层 `archive` 都会通知本库owner，无需每个生成或重拍脚本分别实现压缩。

每日检查发布的 `release-automation.json.prepare` 先运行 `materialize_package.py`。它调用 `repository_media.py reconcile` 扫描已配置工作台、直接写入的 `entries/**/record.json`、登记载荷及没有登记的媒体文件，自动识别真实格式、无损处理、去重、生成精确版本，并更新代码、集合、预览与人物尺度的引用。最后刷新内容锁，再沿现有Framework OCI流程发布媒体和轻量软件包。

裸文件按实际文件名、SHA-256、路径和可测得尺寸自动生成技术记录，缺少用途或许可证据就如实保留待补，视觉、医学与听感仍保持待审。信息欠项不阻断整批整理；单项数据或编码问题保留原件和具体说明，其他素材继续处理。已有审查决定随精确版本迁移，不把格式整理当作质量批准。

图片统一尝试无损WebP，逐像素核对完整RGBA（包括全透明处的RGB）及ICC配置；原尺寸、Alpha、锚点和内容bounds保持一致。16位、动画PNG及WebP无法完整承载的PNG颜色信息保留原格式。整数PCM WAV尝试FLAC，核对解码采样哈希、采样率和声道。JPEG、MP4、MP3等既有压缩格式不重复有损转码；转换后不更小则使用原格式。处理按“来源SHA-256＋策略”缓存，同一字节只编码一次。

仓库内保留可直接使用的压缩版本视图和元数据；母版、来源证据与唯一媒体对象保存在仓库外的持久目录。默认目录为 `~/.local/share/mac-media-assets/media`，配置与工作台登记在同层 `libraries.json`，测试或其他机器可用 `MAC_MEDIA_STATE` 指定位置。视图在同盘使用只读硬链接，同一内容占一份数据；项目导入是可编辑的独立副本。大型历史Git对象保持原历史，不以本次整理重写历史或承诺旧克隆自动缩小。

源头登记会立即处理新增记录；每日全仓扫描负责补上绕过入口的直接写入。`query`、`plan`、`audit` 和 `materialize_package.py --check` 只读；真正的日常 `prepare` 主动完成整理。没有另外建立以“格式不对就拒绝提交”为主要手段的流程。

媒体的OCI artifact沿用同一公开 `mac-media-assets` 软件包仓库，以内容指纹固定media标签，并用Framework的 `oci-publication-preflight.mjs` 回读digest、来源和匿名可读性。轻量软件包记录固定manifest digest及媒体SHA-256，按需取用直接读取已发布的对象；完整包使用同一对象。原始母版不进入轻量包。OCI发布只由已授权的正式发布流程执行，本地整理与远端发布分别记录。

```sh
# 日常prepare：自动处理漏入、规范化、压缩和引用，再刷新内容锁。
python3 tools/materialize_package.py
# 单独执行同一整理；反复运行复用既有结果。
python3 tools/repository_media.py reconcile
# 只读查看当前仓库与对象状态。
python3 tools/repository_media.py audit
# 在本机首次登记工作台；可指定已经完成创作的历史批次补处理。
python3 tools/repository_media.py configure --source-library <工作台/assets/paper-theatre> --backlog <批次回执.json>
# 按现有入口生成完整离线包，使用相同压缩对象。
python3 tools/optimize_media.py --export <库外新目录> --archive <完整离线包.tar.gz>
```

独立人物、器官和可拼接部件是否透明、内容是否合适，仍由实际素材与当前镜头审看决定。存储整理只改变编码和路径；作者形象、声线、品牌和签名音乐继续保管在私有作者工作区，不随通用库公共同步。

> Git 跟踪分层说明：仓库默认只随 Git 跟踪轻量核心元数据和随包组件、CI 动作测试件及 README 展示样例；其余已发布至 OCI 的 `payloads/` 已切出 Git 跟踪并纳入 `/payloads/` 忽略列表，通过 `tools/repository_media.py reconcile` 在本机以 APFS/同盘只读硬链接方式刷新零额外占用的本地预览视图。一次性专题研究生成与试装脚本统一归档在 `scripts/studies/`，`tools/` 保留稳定 CLI 与日常运行管线。
