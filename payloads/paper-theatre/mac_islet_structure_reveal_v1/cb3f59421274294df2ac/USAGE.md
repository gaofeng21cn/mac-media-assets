# 胰岛·逐层揭示与局部高亮

胰岛局部组织关系示意：中央为成簇内分泌细胞，周围为外分泌腺泡，毛细血管在细胞间分支。颜色不指定细胞类型，数量与分布不代表真实比例；不是胰腺整器官总览，不表达分泌或血糖调节。 仅二维揭示和高亮；不表示连续剖开、三维旋转或生理运动。

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_islet_structure_reveal_v1@<revision>
```

本地HTTP打开index.html；通过sequence.json编辑层序、节奏与整组相机；renderStudy可接入Canvas。保留所有图层共同原点，不按bounds独立居中；医学与当前镜头仍待终审。
