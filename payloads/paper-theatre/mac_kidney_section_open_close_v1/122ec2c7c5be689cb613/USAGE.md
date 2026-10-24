# 肾脏·冠状剖面开合连续开合

单肾冠状切面，分开皮质背景、髓质锥体和肾盂/肾盏/输尿管；不表示肾单位微观滤过、血管或精确肾盏数。远景版仅表达肾与输尿管身份。 既有冠状剖面内部连续打开；不表达肾单位与滤过。 

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_kidney_section_open_close_v1@<revision>
```

本地HTTP打开index.html；renderStudy可直接接入Canvas。section配置保存每个边界、枢轴和原图依据；timing控制打开、保持与关闭。保留图层与窗口共同原点；不能把位置图改名为真实切面。
