# 盆腔器官·盆腔前后投影揭层连续开合

女性盆腔正面投影示意，子宫连输卵管与两侧卵巢；膀胱为前方半透明投影，直肠为后方虚线投影。前后深度需结合侧视图解释，非同一冠状切面。 前方投影局部隐去以看后方；不是同一冠状切面。 前后器官用半透明/虚线投影表达，并非同一冠状切面；只能揭开投影，不能称盆腔切开。

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_pelvic_organs_section_open_close_v1@<revision>
```

本地HTTP打开index.html；renderStudy可直接接入Canvas。section配置保存每个边界、枢轴和原图依据；timing控制打开、保持与关闭。保留图层与窗口共同原点；不能把位置图改名为真实切面。
