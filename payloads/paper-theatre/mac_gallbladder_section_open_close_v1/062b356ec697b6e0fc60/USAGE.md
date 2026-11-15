# 胆囊·二维剖面开合连续开合

胆囊外形与胆汁示意；不表示胆囊内结石、胆道梗阻或胆囊功能。 胆囊壁局部窗口连续开合；不表达结石、功能或流动。 

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_gallbladder_section_open_close_v1@<revision>
```

本地HTTP打开index.html；renderStudy可直接接入Canvas。section配置保存每个边界、枢轴和原图依据；timing控制打开、保持与关闭。保留图层与窗口共同原点；不能把位置图改名为真实切面。
