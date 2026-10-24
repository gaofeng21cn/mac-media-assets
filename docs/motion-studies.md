# 可复用动作包

[完整样片与交互预览](../tools/preview-engine/motion.html)可按角色、结构和动作筛选。页面默认静止，点击后播放；每套保留原图、可编辑源码、精确版本、完整样片、浅深彩底、手机宽和输入绑定的审看记录。

## 人物、监测与生活

| 动作 | 精确版本 |
| --- | --- |
| 同身份成年男性双侧步态循环 | `paper:mac_walk_cycle_v1@9139c228977b8bccb2fa` |
| 同身份坐下、坐定与起立完整过渡 | `paper:mac_sit_stand_cycle_v1@d6c4133126cf5168fa45` |
| 双人照护：接近、协助起身、伴行与松手 | `paper:mac_care_assistance_v1@7add8a71f20bb1997826` |
| 连续备餐：切配、入锅、翻动与盛出 | `paper:mac_cooking_action_v1@4e1f3848364c56d2fe6e` |
| 上臂式血压计：贴合袖带、静止测量与取下 | `paper:mac_bp_cuff_action_v1@cd76e767f879e3b37fca` |
| 血糖仪操作：插试纸、采血、读数与按压止血 | `paper:mac_glucose_test_action_v1@22e327c4f455cc309c19` |
| 动态血压：佩戴、固定、试测、日夜记录与交回 | `paper:mac_abpm_wear_cycle_v1@7b24ce96e85f54d216d5` |
| 儿童女性·落座、取报告与起身 | `paper:mac_child_girl_seat_report_stand_v1@ea17c5496558afc3cc7e` |
| 孕妇·落座、取报告与起身 | `paper:mac_pregnant_woman_seat_report_stand_v1@aaa95674cb25cdcd55bd` |
| 年轻成年男性·落座、取报告与起身 | `paper:mac_young_man_seat_report_stand_v1@4e5c056cff995065ec14` |
| 成年女性·落座、取报告与起身 | `paper:mac_adult_woman_seat_report_stand_v1@77bc7e9970af24261d42` |
| 男性青少年·落座、取报告与起身 | `paper:mac_teen_boy_seat_report_stand_v1@76c3699af8be9bb96442` |
| 男童·落座、取报告与起身 | `paper:mac_child_boy_seat_report_stand_v1@68c39c6ac1663f417401` |
| 老年女性·落座、取报告与起身 | `paper:mac_older_woman_seat_report_stand_v1@e0e53e0208f7f965b056` |
| 老年男性·落座、取报告与起身 | `paper:mac_older_man_seat_report_stand_v1@581f15b28a8f6e9b757c` |
| 青少年女性·落座、取报告与起身 | `paper:mac_teen_girl_seat_report_stand_v1@b15d25f5a56c1d9c79b0` |
| 老年女性·床沿落座、侧卧休息与起身 | `paper:mac_older_woman_bed_rest_v1@2aca41d871b651678db8` |

九类新增角色为同身份八姿态纸上表演：站稳、屈膝、下降、坐定、触纸、持纸、准备起身、站立持纸。人物、椅子和小桌构成完整接触单元，所有状态沿同一身体像素标尺与人工核对的同一椅脚配准。床包为六姿态自主休息，床沿、枕头、床垫和人物保持共同变换。家具不能拆出独立缩放；这些坐站/持物样片不等同于新增步态循环。

普通轻扶照护与床休息不承担失能搬运、术后转移或急救操作教学。血糖包保持试纸连接，包含采血笔接触和按压；袖带贴合裸露上臂。新版动态血压包补齐佩戴、固定、静止试测、日夜记录与交回，记录点仅表示过程。旧毛衣上套袖带的静态人物和旧ABPM记录包已退出默认推荐。

## 结构逐层揭示与连续开合

18类结构各有逐层揭示/原位高亮，以及连续开合或同位关系揭层。7类支持二维局部剖面，动脉壁为既有横断面扇区展开，其余10类按实际内容提供位置/关系揭层；红细胞中央淡区仍是完整胞质，不是内腔。

| 结构 | 逐层揭示 | 连续开合/揭层 |
| --- | --- | --- |
| 甲状腺 | `paper:mac_thyroid_structure_reveal_v1@8b3d44b3cb76a745b3ee` | `paper:mac_thyroid_section_open_close_v1@862a57d9533341f457b0` |
| 肾脏 | `paper:mac_kidney_structure_reveal_v1@934d8f457b792794a078` | `paper:mac_kidney_section_open_close_v1@122ec2c7c5be689cb613` |
| 动脉壁 | `paper:mac_artery_wall_structure_reveal_v1@5533f7ee96339311a399` | `paper:mac_artery_wall_section_open_close_v1@178b110d0e1a997d7e8e` |
| 胰腺与胰管 | `paper:mac_pancreas_structure_reveal_v1@821ee89da2074949aca9` | `paper:mac_pancreas_section_open_close_v1@51ffac1e004bdbbee6b1` |
| 垂体与邻近结构 | `paper:mac_pituitary_structure_reveal_v1@12e57ad343774b8f2f8d` | `paper:mac_pituitary_section_open_close_v1@0eb59b3dc64ba920ea95` |
| 心脏 | `paper:mac_heart_structure_reveal_v1@0940630b475c6588a8ad` | `paper:mac_heart_section_open_close_v1@4aa9cb4d9c688b5c12da` |
| 肺与气管 | `paper:mac_lungs_structure_reveal_v1@dce590c5e7cd40f29332` | `paper:mac_lungs_section_open_close_v1@2c2e3b116be59c7f9a4f` |
| 肝脏 | `paper:mac_liver_structure_reveal_v1@d28edb53e8382bd46610` | `paper:mac_liver_section_open_close_v1@591d7339b0ed37611608` |
| 胃 | `paper:mac_stomach_structure_reveal_v1@701d7f8ddf88581146d6` | `paper:mac_stomach_section_open_close_v1@ca640885e9270095f328` |
| 肠道 | `paper:mac_intestine_structure_reveal_v1@86c7d25bc8f1f25e4e6a` | `paper:mac_intestine_section_open_close_v1@534f61d8fa23cb0943d1` |
| 胆囊 | `paper:mac_gallbladder_structure_reveal_v1@9356add0ed20b63a4ccf` | `paper:mac_gallbladder_section_open_close_v1@9e7ecd62ae85bff8345a` |
| 胰岛 | `paper:mac_islet_structure_reveal_v1@ac4e9c5a278ddd96ab92` | `paper:mac_islet_section_open_close_v1@1bb269fe1729888b0944` |
| 肺泡 | `paper:mac_alveolus_structure_reveal_v1@42ff22a34117b3081b47` | `paper:mac_alveolus_section_open_close_v1@7e6c7b286ccaca3e71db` |
| 红细胞 | `paper:mac_blood_cell_structure_reveal_v1@525d83d9970afe13ed03` | `paper:mac_blood_cell_section_open_close_v1@f3755eb49a37f839362c` |
| 乳腺 | `paper:mac_breast_structure_reveal_v1@c2c652dca8011d8947c2` | `paper:mac_breast_section_open_close_v1@d647c84c7bf46425f637` |
| 足关节 | `paper:mac_foot_joint_structure_reveal_v1@c8fb38bd7e928a833230` | `paper:mac_foot_joint_section_open_close_v1@ef45083320cdce37f5fa` |
| 盆腔器官 | `paper:mac_pelvic_organs_structure_reveal_v1@b1685ac65b2a189e40e4` | `paper:mac_pelvic_organs_section_open_close_v1@24bfc53bee095872189c` |
| 头部矢状位 | `paper:mac_head_sagittal_structure_reveal_v1@ce3141ba0ce1ceb13d9b` | `paper:mac_head_sagittal_section_open_close_v1@a0165244ab3195e818b9` |

开合窗口受原结构边界约束，内部与外层保留共同原点，关闭恢复初始主体。肾门至输尿管保持连续，切口线与外层真实alpha相交，组织切面在深底仍保持原始不透明色。不同视角的原图通过切镜连接。

## 发现、真实取用与接入

前两条在素材库查询；取用命令在MAC制作工作区运行。

```bash
python3 tools/query_assets.py --category motion --character-role 老年男性 --action 坐站过渡 --json
python3 tools/query_assets.py --category motion --query 肾脏 --json
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:<ID>@<revision>
```

动作进入工程的 `src/library/<ID>/<revision>/`。加载复制后的图片与sequence.json，调用 `renderStudy(ctx, images, sequence, seconds)`；本集控制时间并支持随机seek。图集rect为整图坐标，origin为帧内坐标，registration.json保管绑定源SHA的人工配准。真实取用须回读library-record、sequence和载荷字节；当前镜头重新审查。

## 证据与维护

本批47个新动作包和2个简化图修订已全部真实导入独立小样，3092个载荷逐文件SHA一致。此前四套动作的[132载荷取用证据](interaction-review/motion-intake-20261024.json)保留原范围。人物、结构和安装回执分别记录，技术通过不升级为当前生产镜头、听感、独立医学终审或发布通过。

```bash
node tools/check_motion_studies.mjs
python3 tools/verify_catalog.py
```

固定接触包的确定性检查绑定原图SHA、源矩形、人工锚点、统一身体标尺与终点保持。动作质量由实际状态、切换两侧和多底色复核判断；旧render不覆盖新源码。新字节登记新revision，历史原件保持不可变。

## 配套拟音

5套动作拟音各有3个变体：脚步、落座、衣料、器械完成提示与烹饪油声。可从[声音入口](../tools/preview-engine/audio.html)逐一试听；它们是程序合成。原声、真实旁白混音和当前镜头的最终音轨分别实际审听后记录，波形与无削波只提供技术证据。
