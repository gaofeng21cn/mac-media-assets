# 动脉壁·横断面扇区展开连续开合

动脉横断面三层壁与管腔，外膜、中膜、内膜逐层套叠；层厚只为可读性，无狭窄/斑块或病理含义，不能用于厚度测量。 既有横断面的连续扇区展开；不冒充三维血管切开。 原件已是三层壁横断面，不含外观到切面的形态；提供横断面内的连续扇区分层展开。

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_artery_wall_section_open_close_v1@<revision>
```

本地HTTP打开index.html；renderStudy可直接接入Canvas。section配置保存每个边界、枢轴和原图依据；timing控制打开、保持与关闭。保留图层与窗口共同原点；不能把位置图改名为真实切面。
