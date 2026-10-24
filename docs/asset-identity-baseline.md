# 生产基线身份

2026-10-24 建立。库里的角色素材已经够用，但生产侧此前长期使用两张从未入库的
欧美水彩人物（`body` 74 集、`walking` 74 集），库里已策展的中国形象只覆盖少量集。
本表把「一个角色在生产里只能用哪一个人」变成机器可查的登记，替换时不再靠记忆挑图。

权威数据在 `collections/character-identity-baseline.json`，由
`tools/build_identity_baseline.py` 生成与自校验（`--check` 只读），
`tools/query_identity.py` 供检索。身份判定来自逐张查看原件比对脸部、发型、服装与体型，
不按文件名或修订顺序推断。

## 生产基线

| 角色 | 身份家族 | 可用姿态 |
| --- | --- | --- |
| 成年女性患者 | `adult_woman_cn_mustard`（芥黄开衫＋青绿长裤） | 站、步行、坐、伸手、侧站、卧、照护伸手、持手机呼叫 |
| 成年男性患者 | `adult_man_cn_green_red`（绿衫红裤） | 站、步行、坐、伸手、上腹坐凳、扶手椅两种状态 |
| 儿童／青少年／年轻成年／老年 | `child_girl_cn`、`child_boy_cn`、`teen_girl_cn`、`teen_boy_cn`、`young_man_cn`、`older_man_cn`、`older_woman_cn` | 各角色四姿态；老年男女另有站坐转换中间姿态、扶杖与轮椅整件 |
| 孕妇 | `pregnant_woman_cn` | 四姿态；与成年女性基线视觉同源，属体型变体，同镜出现需明确区分 |
| 主讲医生 | 作者私有库（不进公共库） | 站讲解、坐姿问诊、步行、伸手 |
| 其他身份的医生 | `clinician_man_cn`、`clinician_woman_cn` | 站讲解、坐姿问诊、步行、伸手；必须显式选择，不与讲者混用 |

## 未准入的生产人物

`body`、`walking`、`body-paper-study-v1` 从未入库：没有族裔、身份家族、锚点与审看边界，
且与面向国内观众的既定中国形象方向、整季纸剪贴语言都不一致。逐集替换清单见制作工作区
`work/review/identity-baseline-20261024/episode-replacement-plan.json`（含文件与行号），
对照图 `identity-comparison.jpg`。**该表只提供机械事实与候选身份；这个人物在本集是患者本人、
家属还是他人，仍由各集导演按剧本判定。**

## 家族内已识别的漂移

- `character_teen_girl_stand_v1` 的另一个修订版是长直发黄外套少女，与本家族不是同一人。
- `character_adult_man_seated_v1` 的另一个修订版为深绿衫蓝裤，与红裤家族下装不同。
- `reserve_person_pointing_v1`（蓝西装讲解）与 `reserve_person_lying_v1`（蓝白背心卧姿）
  原属通用人物，已单列为独立身份，不并入成年女性基线。

这些成员保留在库内可查，但不进入生产推荐。登记只覆盖生产基线家族；其余已登记角色资产
尚未逐件核对身份一致性。

## 边界

本表决定「用哪个人」，不决定当前镜头是否通过。尺寸、接触、遮挡、医学含义与听感仍按各自
职责审看；9类新增坐站/持纸完整接触序列和床休息已补可播放样片，身体标尺与家具锚点绑定精确原图。实际可播放范围见 motion-studies.md，静态步行姿态与完整步态分别记录。
