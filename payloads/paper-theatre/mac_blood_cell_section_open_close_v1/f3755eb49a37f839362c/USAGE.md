# 红细胞·中央淡区连续揭示连续开合

红细胞双凹圆盘正视示意，区分膜、胞质与中央淡区；不表示血红蛋白含量、形态学分类或血液病。 中央淡区是正视外观，仍为细胞；不是切开的内腔。 central_pallor 是正视中央淡区，原件没有膜截面或细胞内部剖面；不能把淡区冒充内腔。

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_blood_cell_section_open_close_v1@<revision>
```

本地HTTP打开index.html；renderStudy可直接接入Canvas。section配置保存每个边界、枢轴和原图依据；timing控制打开、保持与关闭。保留图层与窗口共同原点；不能把位置图改名为真实切面。
