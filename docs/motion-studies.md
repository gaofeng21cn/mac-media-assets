# 四套连续动作

2026-10-24 补齐此前明确列出的连续步态、坐站过渡、照护全过程和连续烹饪四类缺口。它们是有发展和结果的完整动作包；原有静态姿态保留各自原审看范围。

[观看完整样片与交互预览](../tools/preview-engine/motion.html)。从库根启动本地 HTTP 服务后打开该页，每包可播放、随机拖动和切换浅/深/彩底。人物使用完整姿态逐帧表演，烹饪中的接触层和道具独立运动。

| 动作 | 完整过程 | 精确版本 |
| --- | --- | --- |
| 双侧步态，6秒 | 站稳→两次八帧双侧循环→站稳；位移与姿态共用逐帧时钟 | `paper:mac_walk_cycle_v1@9139c228977b8bccb2fa` |
| 坐站过渡，6秒 | 站立→屈膝→降低→坐定→前倾→伸展→站稳，固定椅子独立 | `paper:mac_sit_stand_cycle_v1@d6c4133126cf5168fa45` |
| 日常轻扶照护，6.5秒 | 接近→示意→轻扶→患者主动起身→稳立→伴行一步→落定→松手 | `paper:mac_care_assistance_v1@7add8a71f20bb1997826` |
| 连续备餐，9秒 | 三次刀刃接触→三片→入锅→连续翻动→三片盛盘 | `paper:mac_cooking_action_v1@4e1f3848364c56d2fe6e` |

步态、坐站和照护沿浅绿衫红裤虚构男性身份准备。步态按每姿态0.25秒表演，成片24fps；这是可编辑的纸剧场逐帧风格。照护包的双人和椅子属于完整姿态整体帧，可整体放置，需改变双方接触时重做对应姿态。坐站包的椅子、烹饪包的手/器具/食材可以独立调整。

日常轻扶照护表达能主动借腿与扶手起身者的陪伴过程；临床失能转移、术后搬运和急救教学另有操作规范。备餐样本表达物件接触和数量变化，真实加热时间、温度、熟度和食品安全信息由具体故事提供。样本无声。

## 发现和取用

```bash
python3 tools/query_assets.py --category motion --query 连续动作
python3 tools/query_assets.py --collection walk_cycle
```

在 MAC 制作工作区调用既有入口，`--root` 使用实际安装的公共库路径，`--project` 使用当前工程相对路径：

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_walk_cycle_v1@9139c228977b8bccb2fa
```

四套包均已真实查询并导入独立小样工程，回读复制的精确版本、原记录、逐帧坐标和源文件哈希；[取用回执](interaction-review/motion-intake-20261024.json)记录132个载荷的逐文件核对。动作属于 `motion_recipe`，导入至 `src/library/<id>/<revision>/`，时间线和帧配准在 `sequence.json` 中；它们不向图像 manifest 伪造单件人物锚点。导入保留来源审看，当前镜头状态为 `pending`。

开发者可沿 `viewer.mjs` 加载本地图片和 `sequence.json`，调用 `runtime.mjs` 的 `renderStudy(ctx, images, sequence, seconds)` 接入本集 Canvas。时间由本集提供，支持任意 seek。帧的 `rect`、`origin`、`reference_height` 共用原件像素坐标；`events` 记录接触时点。新镜头调整比例、地面、椅面及手持物关系时重新试装。

## 审看和维护

每包保存原始生成图、所复用公共原件的精确版本和 SHA-256、生成请求说明、可编辑源码、完整 MP4、全部关键姿态、正常播放采集总览、三底色与手机图。原图保留生成字节，裁切仅通过运行时源矩形进行。

模型实际查看上述画面后写入 `review.json`，绑定输入及样片哈希。技术记录只核对渲染、浏览器错误、随机 seek 和文件身份；当前故事的医学、声音和发布审查继续由各自职责持有。人物、样片和来源均为公共内容，Dr.咩 私有形象不在这些包内。

```bash
node tools/check_motion_studies.mjs
python3 tools/verify_catalog.py
```

前者检查终点保持、姿态遍历、刀刃接触前不出切片、三片守恒及转运边界连续性；视觉语义以各包实际审看记录为据。重新生成候选可使用 `tools/build_motion_studies.py prepare`；生成图片由内建图像生成工具提供。`tools/render_motion_studies.mjs` 使用显式指定的 Playwright 模块和本地 HTTP 根渲染。`freeze` 只接受已经完成实际审看且源文件/媒体哈希未改变的候选，新字节注册新 revision。
