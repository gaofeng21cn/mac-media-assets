# 胰腺与胰管·逐层揭示与局部高亮

概念性胰腺外形与主胰管示意，画面左侧为胰头、右侧为胰尾；并非患者影像。胰管分支只表达汇流关系，不表达精确分支数；不包含胆管、十二指肠、胰岛或微观细胞，不能演示手术、病灶或内分泌细胞比例。 仅二维揭示和高亮；不表示连续剖开、三维旋转或生理运动。

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_pancreas_structure_reveal_v1@<revision>
```

本地HTTP打开index.html；通过sequence.json编辑层序、节奏与整组相机；renderStudy可接入Canvas。保留所有图层共同原点，不按bounds独立居中；医学与当前镜头仍待终审。
