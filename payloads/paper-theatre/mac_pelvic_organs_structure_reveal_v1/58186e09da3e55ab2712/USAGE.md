# 盆腔器官·逐层揭示与局部高亮

女性盆腔正面投影示意，子宫连输卵管与两侧卵巢；膀胱为前方半透明投影，直肠为后方虚线投影。前后深度需结合侧视图解释，非同一冠状切面。 仅二维揭示和高亮；不表示连续剖开、三维旋转或生理运动。

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_pelvic_organs_structure_reveal_v1@<revision>
```

本地HTTP打开index.html；通过sequence.json编辑层序、节奏与整组相机；renderStudy可接入Canvas。保留所有图层共同原点，不按bounds独立居中；医学与当前镜头仍待终审。
