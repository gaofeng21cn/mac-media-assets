# 乳腺·侧视局部剖面连续开合

乳腺侧视外形示意，附腺体区与乳管走向；不表示肿块大小、分期或触诊结论。 乳房侧视剪纸揭面；腺体区和乳管为位置示意。 

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_breast_section_open_close_v1@<revision>
```

本地HTTP打开index.html；renderStudy可直接接入Canvas。section配置保存每个边界、枢轴和原图依据；timing控制打开、保持与关闭。保留图层与窗口共同原点；不能把位置图改名为真实切面。
