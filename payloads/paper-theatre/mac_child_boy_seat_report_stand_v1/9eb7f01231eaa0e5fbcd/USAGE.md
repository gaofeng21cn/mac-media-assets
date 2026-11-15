# 男童·落座、取报告与起身

同身份完整人物与家具接触单元；纸上八姿态切换，支持落座、取纸与起身。不是步态循环或临床转移教学；改变家具或持握关系须重做对应姿态。

## 取用

```bash
python3 scripts/media_asset_library.py use --root <公共库路径> \
  --project <本集工程路径> --id paper:mac_child_boy_seat_report_stand_v1@<revision>
```

显式调用renderStudy；同一身体标尺与帧内家具锚点共同变换，完整单元不可拆成独立椅子或手臂。
