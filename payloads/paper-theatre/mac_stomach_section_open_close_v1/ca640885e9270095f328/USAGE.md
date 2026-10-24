# 胃·二维剖面开合连续开合

胃正面关系示意，画面右侧为胃底和胃体，食管入口在上，幽门向画面左侧延续；胃腔与胃壁分别揭示。不表达胃壁组织层、真实容积或胃排空功能。 胃壁剪纸窗口连续开合，胃腔保持连通；不表达蠕动。 

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_stomach_section_open_close_v1@<revision>
```

本地HTTP打开index.html；renderStudy可直接接入Canvas。section配置保存每个边界、枢轴和原图依据；timing控制打开、保持与关闭。保留图层与窗口共同原点；不能把位置图改名为真实切面。
