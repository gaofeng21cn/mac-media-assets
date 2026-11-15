# 动脉壁·逐层揭示与局部高亮

动脉横断面三层壁与管腔，外膜、中膜、内膜逐层套叠；层厚只为可读性，无狭窄/斑块或病理含义，不能用于厚度测量。 仅二维揭示和高亮；不表示连续剖开、三维旋转或生理运动。

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_artery_wall_structure_reveal_v1@<revision>
```

本地HTTP打开index.html；通过sequence.json编辑层序、节奏与整组相机；renderStudy可接入Canvas。保留所有图层共同原点，不按bounds独立居中；医学与当前镜头仍待终审。
