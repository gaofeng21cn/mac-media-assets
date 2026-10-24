# 肺泡·二维剖面开合连续开合

单个肺泡与相连气道的放大关系示意：气腔连续、薄壁在外、毛细血管环绕壁外。壁厚与血管间距为说明而夸张，双色仅区分血管路径，不表达氧含量、流向或气体交换数值。 肺泡与气道连续气腔揭开；不表达呼吸或气体交换。 

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_alveolus_section_open_close_v1@<revision>
```

本地HTTP打开index.html；renderStudy可直接接入Canvas。section配置保存每个边界、枢轴和原图依据；timing控制打开、保持与关闭。保留图层与窗口共同原点；不能把位置图改名为真实切面。
