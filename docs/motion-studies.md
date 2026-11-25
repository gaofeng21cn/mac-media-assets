# 可复用动作包

[完整样片与交互预览](../tools/preview-engine/motion.html)可按角色、结构和动作筛选。页面默认静止，点击后播放；每套保留原图、可编辑源码、精确版本和样片。当前策展标明实际审看范围；原审看记录仅用于追溯。

## 人物、监测与生活

| 动作 | 精确版本 |
| --- | --- |
| 同身份成年男性双侧步态循环 | `paper:mac_walk_cycle_v1@145fd0a1ed9fed47bffd` |
| 双人照护：接近、协助起身、伴行与松手 | `paper:mac_care_assistance_v1@0824456d2c4a3030b477` |
| 连续备餐：切配、入锅、翻动与盛出 | `paper:mac_cooking_action_v1@42d682eb6e16a5bcf8e4` |
| 上臂式血压计：贴合袖带、静止测量与取下 | `paper:mac_bp_cuff_action_v1@8828a69c69d7506f2fe9` |
| 血糖仪操作：插试纸、采血、读数与按压止血 | `paper:mac_glucose_test_action_v1@21bc641c6ab3e57b9124` |
| 动态血压：佩戴、固定、试测、日夜记录与交回 | `paper:mac_abpm_wear_cycle_v1@6ea5d67a895bc526e5b1` |
| 儿童女性·落座、取报告与起身 | `paper:mac_child_girl_seat_report_stand_v1@dcec43d66138230ec3ff` |
| 孕妇·落座、取报告与起身 | `paper:mac_pregnant_woman_seat_report_stand_v1@dbdf3f8b1b8d4da0dd12` |
| 年轻成年男性·落座、取报告与起身 | `paper:mac_young_man_seat_report_stand_v1@ac16dc26346a141b72a7` |
| 成年女性·落座、取报告与起身 | `paper:mac_adult_woman_seat_report_stand_v1@e083d01cdecb8a8c3bfc` |
| 男性青少年·落座、取报告与起身 | `paper:mac_teen_boy_seat_report_stand_v1@026befb03059088054a6` |
| 男童·落座、取报告与起身 | `paper:mac_child_boy_seat_report_stand_v1@9eb7f01231eaa0e5fbcd` |
| 老年女性·落座、取报告与起身 | `paper:mac_older_woman_seat_report_stand_v1@4174f7197beae2897bc7` |
| 老年男性·落座、取报告与起身 | `paper:mac_older_man_seat_report_stand_v1@b33ca88b838e81d699ae` |
| 青少年女性·落座、取报告与起身 | `paper:mac_teen_girl_seat_report_stand_v1@ea686c0841f587a08ce5` |
| 老年女性·床沿落座、侧卧休息与起身 | `paper:mac_older_woman_bed_rest_v1@192c18c68bd1ad5696fd` |

坐站持纸接触单元为同身份八姿态纸上表演：站稳、屈膝、下降、坐定、触纸、持纸、准备起身、站立持纸。人物、椅子和小桌构成完整接触单元，所有状态沿同一身体像素标尺与人工核对的同一椅脚配准。床包为六姿态自主休息，床沿、枕头、床垫和人物保持共同变换。家具不能拆出独立缩放；坐站/持物样片不等同于步态循环。

普通轻扶照护与床休息不承担失能搬运、术后转移或急救操作教学。血糖包保持试纸连接，包含采血笔接触和按压；袖带贴合裸露上臂。动态血压包包含佩戴、固定、静止试测、日夜记录与交回，记录点仅表示过程。旧毛衣上套袖带的静态人物和旧 ABPM 记录包已退出默认推荐。

## 结构逐层揭示与连续开合

各解剖结构提供逐层揭示/原位高亮，以及连续开合或同位关系揭层（支持二维局部剖面、横断面扇区展开或按实际内容提供位置/关系揭层；红细胞中央淡区仍是完整胞质，不是内腔）。

| 结构 | 逐层揭示 | 连续开合/揭层 |
| --- | --- | --- |
| 甲状腺 | `paper:mac_thyroid_structure_reveal_v1@74b2cf269374f032e66f` | `paper:mac_thyroid_section_open_close_v1@7667b1fba0014b663049` |
| 肾脏 | `paper:mac_kidney_structure_reveal_v1@87e27d778734f4cecfd9` | `paper:mac_kidney_section_open_close_v1@b2fb8e841d453a51526e` |
| 动脉壁 | `paper:mac_artery_wall_structure_reveal_v1@ace05efbabd7dc24cc14` | `paper:mac_artery_wall_section_open_close_v1@d3b42c1c811ddd9b5a89` |
| 胰腺与胰管 | `paper:mac_pancreas_structure_reveal_v1@03e53a4d4d44f1093b67` | `paper:mac_pancreas_section_open_close_v1@036b35592e6aba9a38cd` |
| 垂体与邻近结构 | `paper:mac_pituitary_structure_reveal_v1@50c991ff650097866d28` | `paper:mac_pituitary_section_open_close_v1@f7c12568f5541cbebe0d` |
| 心脏 | `paper:mac_heart_structure_reveal_v1@575415b9c0ffd2f3d1b4` | `paper:mac_heart_section_open_close_v1@ae77e13bee9b9b8fb6c1` |
| 肺与气管 | `paper:mac_lungs_structure_reveal_v1@2b7ff940406eddf29d08` | `paper:mac_lungs_section_open_close_v1@1ad8eec277c06e117059` |
| 肝脏 | `paper:mac_liver_structure_reveal_v1@e7e852b962ac2b43adab` | `paper:mac_liver_section_open_close_v1@a7977be33dd96de214ae` |
| 胃 | `paper:mac_stomach_structure_reveal_v1@0c12d2c2490bf53fca6c` | `paper:mac_stomach_section_open_close_v1@cf833d5b245065979315` |
| 肠道 | `paper:mac_intestine_structure_reveal_v1@0455ca73b67bba2a3a7d` | `paper:mac_intestine_section_open_close_v1@e7635ce0fc0ed8682347` |
| 胆囊 | `paper:mac_gallbladder_structure_reveal_v1@ecf0db3d4b2c841a84ad` | `paper:mac_gallbladder_section_open_close_v1@062b356ec697b6e0fc60` |
| 胰岛 | `paper:mac_islet_structure_reveal_v1@cb3f59421274294df2ac` | `paper:mac_islet_section_open_close_v1@e4ae9264b9d2663fc54f` |
| 肺泡 | `paper:mac_alveolus_structure_reveal_v1@adacda649082a0c7b1cb` | `paper:mac_alveolus_section_open_close_v1@5d5aefbc6f034478f5f6` |
| 红细胞 | `paper:mac_blood_cell_structure_reveal_v1@1796d548fd76b770cc4a` | `paper:mac_blood_cell_section_open_close_v1@18b79d483310e3a93876` |
| 乳腺 | `paper:mac_breast_structure_reveal_v1@02d47dbd37c7a53cc3fc` | `paper:mac_breast_section_open_close_v1@20f3ae1dbaa2e6207599` |
| 足关节 | `paper:mac_foot_joint_structure_reveal_v1@39850ead089a20c900ac` | `paper:mac_foot_joint_section_open_close_v1@e4d88e4c8e317e953d94` |
| 盆腔器官 | `paper:mac_pelvic_organs_structure_reveal_v1@58186e09da3e55ab2712` | `paper:mac_pelvic_organs_section_open_close_v1@a8b20ad154ce34674e70` |
| 头部矢状位 | `paper:mac_head_sagittal_structure_reveal_v1@79c69e95851480bbffaf` | `paper:mac_head_sagittal_section_open_close_v1@7439677f2adf4760d14b` |

开合窗口受原结构边界约束，内部与外层保留共同原点，关闭恢复初始主体。肾门至输尿管保持连续，切口线与外层真实 alpha 相交，组织切面在深底仍保持原始不透明色。不同视角的原图通过切镜连接。

## 发现、真实取用与接入

前两条在素材库查询；取用命令在 MAC 制作工作区运行。

```bash
python3 tools/query_assets.py --category motion --character-role 老年男性 --action 坐站过渡 --json
python3 tools/query_assets.py --category motion --query 肾脏 --json
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:<ID>@<revision>
```

动作进入工程的 `src/library/<ID>/<revision>/`。加载复制后的图片与 `sequence.json`，调用 `renderStudy(ctx, images, sequence, seconds)`；本集控制时间并支持随机 seek。图集 rect 为整图坐标，origin 为帧内坐标，`registration.json` 保管绑定源 SHA 的人工配准。真实取用须回读 `library-record`、`sequence` 和载荷字节；当前镜头重新审查。

## 证据与维护

原独立人物/椅子坐站包和早期烹饪包版本已退出取用入口，相关精确版本撤回决定见[比例与接触撤回审计收据](quality-audit-2026-11-01.md)。现役动作包仅保留有依据的审看范围，原始包内的历史批量 passed 不再作为取用结论；技术通过不升级为当前生产镜头、听感、独立医学终审或发布通过。

```bash
node tools/check_motion_studies.mjs
python3 tools/verify_catalog.py --metadata-only
```

固定接触包的确定性检查绑定原图 SHA、源矩形、人工锚点、统一身体标尺与终点保持。动作质量由实际状态、切换两侧和多底色复核判断；旧 render 不覆盖新源码。新字节登记新 revision，历史原件保持不可变。

轻量 Git 检出须保留检查器读取的现役动作 `sequence.json`，以及参加检查的运行时、配准文件和源图。整理 Git 载荷时用干净检出运行上述动作检查，本机媒体缓存会补齐缺失文件。

## 配套拟音

脚步、落座、衣料、器械完成提示与烹饪油声等动作拟音及其变体可从[声音入口](../tools/preview-engine/audio.html)逐一试听；它们是程序合成。原声、真实旁白混音和当前镜头的最终音轨分别实际审听后记录，波形与无削波只提供技术证据。
