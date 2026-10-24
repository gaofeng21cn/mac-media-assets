# 动态血压：日夜周期记录与交回设备

演示已正确佩戴后日夜周期记录，24 小时压缩成 8 秒；点列代表采样时点，不是血压数值或真实测量频率。佩戴操作与当前镜头另审。

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_abpm_recording_v1@<revision>
```

复制后显式接入 renderStudy，时间由镜头传入；本包医疗审核 pending。
