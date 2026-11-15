# 心脏·二维剖面开合连续开合

心脏正面四腔关系示意，画面左为解剖右；右房右室与左房左室分别表达。血管为连接概览，未表达瓣膜细节、血流动画或真实比例。 正面四腔剖面剪纸开合；不表达瓣膜与血流运动。 

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_heart_section_open_close_v1@<revision>
```

本地HTTP打开index.html；renderStudy可直接接入Canvas。section配置保存每个边界、枢轴和原图依据；timing控制打开、保持与关闭。保留图层与窗口共同原点；不能把位置图改名为真实切面。
