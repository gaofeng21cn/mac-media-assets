# 上臂式血压计操作动作包

器械操作部件级样本：手臂、袖带与主机各自独立可调，接触点固定在同一条上臂。读数是示意，不表示真实测量时长、测量方法或任何医学结论；临床测量数值与流程由具体故事提供。

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_bp_cuff_action_v1@<revision>
```

导入后位于 `src/library/<id>/<revision>/`，`sequence.json` 记录每层的边界与事件时点，`runtime.mjs` 的 `renderStudy(ctx, images, recipe, seconds)` 可直接接进本集 Canvas，时间由本集提供。

## 边界

手臂、袖带与主机都是独立部件，改比例或落点时重新试装；读数卡是示意，不表示真实测量时长、测量方法或任何医学结论。
