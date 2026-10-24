# 血糖仪操作：插试纸、采血、读数与按压止血

通用指尖血糖采样关系示意，时间被压缩；实际操作沿设备说明。独立医学终审与当前镜头仍待审。

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_glucose_test_action_v1@<revision>
```

导入后位于 `src/library/<id>/<revision>/`，`sequence.json` 记录每层的边界与事件时点，`runtime.mjs` 的 `renderStudy(ctx, images, recipe, seconds)` 可直接接进本集 Canvas，时间由本集提供。手、血糖仪、试纸与敷料都是独立部件，改比例或落点时重新试装。
