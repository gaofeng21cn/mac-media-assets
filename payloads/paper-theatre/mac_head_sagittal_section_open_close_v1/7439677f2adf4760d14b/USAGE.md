# 头部矢状位·头部位置图揭层连续开合

头部向画面右的矢状位关系示意：大脑在颅内、小脑在后下、脑干向下，垂体经柄位于脑底，鼻旁窦位于面部后方。仅作位置说明，非影像切面；细节需独立近景，不表达脑沟回、垂体真实大小或病变。 侧面位置图同位揭层；不表示真实颅骨或脑切面。 没有骨/脑膜/脑实质切面层，只有头部侧面位置示意；提供同位的颅面位置图揭层。

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_head_sagittal_section_open_close_v1@<revision>
```

本地HTTP打开index.html；renderStudy可直接接入Canvas。section配置保存每个边界、枢轴和原图依据；timing控制打开、保持与关闭。保留图层与窗口共同原点；不能把位置图改名为真实切面。
