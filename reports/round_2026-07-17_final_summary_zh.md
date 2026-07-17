# ROGII 2026-07-17 轮次 — 中文最终总结（会话 16baec36 延续，放宽提交预算）

用词中性技术性。目标：私榜（**新井** novel wells）排名，final-2 选择与 public/private 场景识别。

## 1. 本轮查清了 v36 什么（task 1）
- v36 = ref **54753209**，public **7.482**，"Codex v36 zero-contact spatial balanced hidden-activation"，
  2026-07-16 05:42 在 joezzzzz 账号提交。
- **溯源结论：source 本地不可复现。** 无对应 joezzzzz kernel；本地 repo / 所有 job 目录 / 整个 `/home`+`/tmp`
  均无 v36 / zero-contact / hidden-activation 源；Codex 本地会话日志止于 07-14，07-15/07-16 无本地会话 → v36
  与 spatial-formation（54723189，07-15）由**后续远程 Codex 会话**产生，本地无痕迹，kernel 很可能已远程删除。
- **分类：** 7.482 落在 overlap/公榜平台带（Gate-Safe 7.212、Hongwei 7.220、teammate affine 7.278/7.294；
  诚实流形是 8-14）。"zero-contact" = 不直接复制 train-TVT（裸复制得 11551 被拒）而用空间/透传架构达到平台。→
  **overlap/公榜对冲类，novel 私榜高回撤风险**，比 Gate-Safe 略弱。**task 5（v36 变体）因无源而阻塞。**

## 2. 关键发现：隐藏 overlap 是 affine 近重复，且 affine 匹配 FP 不安全（task 4）
- **隐藏 overlap 是 affine 近重复，不是精确重复。** B4′（精确 gate `tvt_rmse<0.02`）在 public 上一无所获
  （9.864≈基线），而 Gate-Safe 的 affine overlay 在同一 split 上达 7.212。重查 train 近碰撞：此前误判为"不同井"
  的 8b95d6d1/a2e8e7f6 其实是**同一口井**——其 toe 用精确复制恢复到 **1.1 ft**、affine 到 1.4 ft，已知段一致
  ~2.4 ft。0.02 ft 的 gate 太严约 100 倍；真实近重复一致在 ~1-3 ft，且常有**基准平移**（affine `b` 达 ~100+ ft，
  例 511e1db0↔ce8399b7 已知段差 50.9 ft、toe 恢复 2.6 ft）。这解释了为何裸复制失败而 affine overlay 成功。
- **affine 匹配无法做到 FP 安全 —— 井跟(heel)↔井趾(toe)墙。** 用已知段 affine 拟合残差做 gate **无法**分离真重复
  与 FP：**残差最小**的匹配（efde6ac3↔d085e611，残差 0.74 ft）恰是 toe 发散到 **18 ft** 的 FP；真重复
  (8b95d6d1) 残差 2.36 ft。用 |affine−DWT| 设 cap 也失败（FP 的中位偏差 3.27 ft 反而**小于**某真重复 3.69 ft）。
  **没有任何测试可得信号能区分真 affine 重复与"heel 匹配但 toe 发散"的井**——与全项目同一信息上限。
- **净效应（诚实、novel-heavy 代理 = train 自匹配）：** DWT+affine 覆盖 **净负**：conservative NET −2.9M、
  balanced NET −2.9M（4 个真重复减误差 6.3 万，但 2 个 FP 在各 ~4500 行上增误差 295 万）。FP 损害碾压真重复收益。
- **结论：所有 overlap 玩法（Gate-Safe、v36、任何 DWT+affine）都是对冲，不是诚实升级**；只在 overlap 占优的集合
  上有利，在 novel 集合上净负。这正是"平台在私榜回撤"的机理。

## 3. final-2 风险矩阵与推荐（task 2）—— 重要重构
既然私榜目标是 **novel 井**，novel 集合上所有 overlap 对冲都回撤，`{DWT, 对冲}` 在 novel 上 = 单 DWT。故
**best-of-2 下第二槽用一个多样化的诚实模型比用 overlap 对冲更好**——诚实模型可能在 novel 上超过 DWT，对冲不能。

| 组合 | novel-heavy 私榜（目标） | overlap-heavy 私榜 |
|---|---|---|
| {DWT, Gate-Safe} | 9.5（Gate-Safe 回撤→DWT 兜底） | ~7.2 |
| **{DWT, Sunny}** | **8.9 若 Sunny 稳，否则 9.5**（DWT 兜底） | ~8.9（无 overlap 捕获） |

- **首选推荐：{DWT 9.519 (54453597), Sunny PF90 8.864 (54710185)}。** Sunny 架构诚实（147 处 OOF/GroupKFold，
  无 overlap 复制技巧），8.864 在诚实流形内 → 可信的诚实模型，可能在 novel 上超过 DWT；best-of-2 用 DWT 兜底。
  **在 novel 私榜上 {DWT, Sunny} 弱占优于 {DWT, Gate-Safe}。** 建议锁定前用 Sunny 的 OOF 验证（重型 GPU fork），
  但即便未验证，相对单 DWT 也无 novel 私榜下行。
- **稳健回退：{DWT 9.519, Gate-Safe 7.212 (54289934)}** —— 仅当有理由相信私榜含 overlap 井时选用。
- **不入选：** v36（overlap/spatial，无源）、B4′（基线方差）、spatial-formation 9.150（部分 overlap guard，不可验证）、
  DWT+affine（FP 不安全对冲，被 Gate-Safe 支配）。

## 4. 本轮新提交（ref + public score）
| ref | 候选 | 目的 | public |
|---|---|---|---|
| 54775625 | DWT 确定性基线（optuna n_jobs=1） | 固定可复现基线水平、隔离 affine 贡献 | 待定 |
| 54775626 | DWT + bounded affine overlay | 经验验证：隐藏 overlap 能否在 DWT 基线上被 affine 捕获 | 待定 |

（上一轮 B4′ 54727655 = 9.864。本轮先做 v36 溯源、affine 机理分析（task 4）、风险矩阵（task 2）、Sunny 审计
（task 6），再据结论做上述 2 个诊断提交；不做无解释扫射。scores 出分后回填并更新 final2 推荐的回退槽判断。）

## 5. 哪些候选不再考虑及原因
- **v36 / spatial-formation：** overlap/spatial 对冲，novel 回撤；且**源码不可复现**、不可做变体或审计。
- **B4′：** 基线 optuna 后处理方差（9.864）+ 精确 gate 抓不到 affine overlap → 不入选。
- **DWT+affine（若诊断证实为对冲）：** FP 不安全、novel 净负；作为对冲被更精炼的 Gate-Safe 支配。

## 6. task 3（diff/相关性指纹）限制记录
Gate-Safe / v36 / Sunny / spatial 的 submission.csv **无法获取**（Kaggle API 不提供历史提交文件下载；这些 kernel
远程/已删）。只有 B4′ 与本轮 DWT+affine/detbase 的 csv 可本地复现。可结构化陈述：可见井上所有 overlap 候选都
重建到≈真值（无法互相区分），真正有信息的 toe diff 在隐藏段不可本地观测——已记录为离线环境硬限制。

## 7. 若还剩时间，下一轮最值得做什么
1. **验证 Sunny 的诚实 OOF**（final-2 的枢轴）：在 Kaggle 上 fork `henry_v10_sunny80_blend`（需
   henryjavier 外部数据集 + GPU），dump OOF/内部 CV。若 CV 明显低于 DWT 的 10.40 → Sunny 是更强诚实基线，
   锁定 {DWT, Sunny}；若 ≈ 或更差 → 8.864 为公榜偏好，回退 {DWT, Gate-Safe}。
2. 确认私榜是否含 overlap 井（决定 {DWT,Sunny} vs {DWT,Gate-Safe} 的关键场景）——目前不可从提交探测，
   依赖 novel 目标 + 平台在私榜回撤的先验。
