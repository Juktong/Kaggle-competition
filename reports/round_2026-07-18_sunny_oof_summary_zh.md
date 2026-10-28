# ROGII 2026-07-18 — Sunny OOF 修复与验证 中文总结（会话 276bd506）

链路：`16baec36 → dacc2829 → b2229931 → 99fff121 → 276bd506`。用词中性技术性。

## 0. 是否有 agent 冲突
无。本会话为 276bd506（active），99fff121（idle，直接前驱），无其它 ROGII agent 处于 working。

## 1. 当前是否有任务在跑
无。Sunny OOF 全量运行已 COMPLETE。

## 2. smoke 尝试与状态（smoke-first，遵守 Directive 4）
通过读代码 + smoke 迭代，定位并修复了 **3 个** 独立问题：
1. **`FLAG_MODEL=True` 跳过了训练**（填充 `oof_preds` 的 LightGBM 训练在 `if not FLAG_MODEL:` 内）→ 汇总时
   `oof_preds` 为空 → 原始崩溃。修复：保持 **`FLAG_MODEL=False`**（训练）+ `IS_SUBMISSION=False` + 受控汇总 cell。
2. **`TEST_SIZE` 子集在 ~60min 的逐井 `build_well` 特征循环（cell 5）之后**才生效 → smoke 不快。修复：在
   `build_well` 前对 `hw_paths/train_wids` 早子集（`FLAG_TEST` 守卫）。
3. **`train_lightgbm` 用行级 `KFold`** → 井内泄漏 → OOF CV 偏乐观、与 DWT native-mask 10.40 不可比。修复：改为
   **`GroupKFold`（按井）** 的诚实 CV。
汇总前加了硬断言（`oof_preds` 非空 / 有列 / 与 `len(y)` 一致 / 有限）。**smoke 结果：PASS**（管线已修好）。
成本发现：`FormationPlaneKNN/DenseANCCImputer` 尊重 `train_wids`（快），但全量 `ROGII_train_df.parquet` 读取 +
下游特征合并是 ~60min 固定成本，不随 `TEST_SIZE` 缩小；且 **batch kernel 的 `is_submission1=True` 会跳过 cell-7
的 TEST_SIZE 子集**，故 push 的 smoke 实际按全量数据训练。

## 3. formal/full run 状态与结果
上述 batch 运行等价于 **全量 formal OOF**（735 井 / 358.5 万行，GroupKFold），~130 分钟完成，COMPLETE。
- **Sunny LightGBM 集成 诚实 GroupKFold OOF CV = 10.4732 ≈ DWT 10.3987** → Sunny 的 **GBM 组件并不强于 DWT**
  （诚实特征上的 GBM，落在同一 blend 中性前沿，符合预期）。
- **提交的 "Sunny PF90 beam-mean10"（54710185, 8.864）是物理/beam 模型，不是这个 GBM meta**（运行还产出
  `submission_sunny_physical.csv`）。故 10.47 不描述物理模型的 8.864；物理模型诚实 CV 本轮未单独隔离。提交的 Sunny
  的诚实强度比较仍以 public 8.864 < DWT 9.519 为准（泄漏审计 clean）。
- **DWT + Sunny-GBM blend（行级，735 井对齐、真值校验、0 失配）：corr 0.746、嵌套权重 +0.16（两折稳定为正）、
  样本外 pooled RMSE 增益 +0.076** → 项目史上**第一次出现"强且去相关"的正向诚实 blend 信号**（正权重=真独立信息，
  不是被公榜反复否定的负权重 λ-伪装）。

## 4. 本轮提交与分数
**未新增竞赛提交。** 唯一 Kaggle 运行为 Sunny OOF 诊断 fork（`joezzzzz/rogii-sunny-oof-smoke`，非竞赛提交）。
不提交 DWT+Sunny-GBM blend 的理由：(1) 增益小（~0.9%）且仅本地 OOF——lessons §7 反复表明本地 blend/后处理增益不
迁移公榜；(2) 它是 GBM-meta blend，而 best-of-2 下**选 Sunny-physical（8.864）支配** DWT+GBM blend（即便 +0.076
迁移也只到 ~9.44）；(3) 需重型双管线 notebook（Sunny ~2h）换取一个被支配、不确定的增益。遵守"没有明确决策价值不
为提交而提交"。

## 5. final-2 推荐（不变）
- **novel / mixed（竞赛目标）：`{det-base DWT 54775625, Sunny PF90 54710185}`**（best-of-2；Sunny-physical 为诚实
  上行，public 8.864 < DWT 9.519；DWT 兜底）。
- **overlap-heavy：`{det-base DWT 54775625, Gate-Safe 54289934}`**。
- 排除：qwer/v36/spatial（不可验证/被支配）、B4′/DWT+affine（无捕获/FP 不安全）、DWT+Sunny-GBM blend（被支配）。

## 6. 若还有 pending / 下一步唯一最值得做
无 pending 运行。**下一步唯一最值得做：隔离 Sunny 的物理/beam 模型的诚实 OOF**（它的 8.864 public 说明它才是真正
更强的组件），再做 DWT + physical blend 检验——若该 blend 有稳定正增益且能迁移公榜，才可能成为优于 best-of-2 选择
的单一诚实候选（届时提交 1 个并核对 public）。本轮已把 GBM-meta 这条查清（正但被支配）。
