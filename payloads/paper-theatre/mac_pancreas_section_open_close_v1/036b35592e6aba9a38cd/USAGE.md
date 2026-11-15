# 胰腺与胰管·二维局部剖面连续开合

概念性胰腺外形与主胰管示意，画面左侧为胰头、右侧为胰尾；并非患者影像。胰管分支只表达汇流关系，不表达精确分支数；不包含胆管、十二指肠、胰岛或微观细胞，不能演示手术、病灶或内分泌细胞比例。 胰腺局部剪纸揭面；只示胰管位置，不表达分泌。 

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_pancreas_section_open_close_v1@<revision>
```

本地HTTP打开index.html；renderStudy可直接接入Canvas。section配置保存每个边界、枢轴和原图依据；timing控制打开、保持与关闭。保留图层与窗口共同原点；不能把位置图改名为真实切面。
