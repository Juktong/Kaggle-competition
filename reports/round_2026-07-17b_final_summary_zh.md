# ROGII 2026-07-17b 轮次 — 中文最终总结（会话 16baec36/dacc2829 延续）

用词中性技术性。目标：私榜（新井）final-2 选择。本轮主线 + 备线 A + 备线 B 均执行。

## 1. qwer（54777533, 7.921）查清了什么，能不能用
- **溯源：source 本地不可恢复。** 无 git commit / kernel / Codex 会话匹配 `SHA424e` 或 "qwer"；Codex 本地会话止于
  07-14，qwer 07-17 由远程会话提交，无本地痕迹（同 v36 模式）。`SHA424e` 不解析到任何本地 artifact。
- **可验证部分的判断：** 描述称 "OOF meta target 6.909"。**6.909 的 OOF 低于 overlap 平台（~7.2）**、远低于诚实
  上限（DWT CV 10.40；最强公开诚实模型 ~8.1）→ **诚实 OOF 不可能到 6.909**，该 CV 只能来自把 overlap/train-重复
  泄漏折进 OOF。故 qwer 的 6.909 是**泄漏膨胀的 OOF，不是诚实 CV**；public 7.921 更是**板上最弱的 overlap 玩法**
  （差于 Gate-Safe 7.212、v36 7.482）。
- **结论：不能用作稳健 final slot**（不可验证 + 泄漏 OOF），作为 upside overlap 候选被 Gate-Safe 支配 → **排除出
  final-2 候选池**。

## 2. Sunny PF90（54710185, 8.864）查清了什么，能不能用
- **来源：** `henry_v10_sunny80_blend`（leemarc223，v34 meta）。**泄漏审计 PASSED：** 无 overlap 复制（无
  `TVT_input=train.values`）、无 gold-visible-prefix 泄漏；标准 GroupKFold OOF；LightGBM+CatBoost+XGB 集成 +
  NCC/beam 地质导向前向（`ncc=Hn@Cn.T`，用测试可得输入，诚实）+ Caruana Climber 混合。`TVT_input.values` 只用于
  漂移率特征；`y_test_temp` 是诚实 train-holdout。
- **相对平台：** 8.864 在诚实流形内（8–14），**高于 overlap 平台**（不是 overlap 玩法）→ Sunny 是**真诚实模型，
  很可能强于 DWT**（诚实模型 public≈private；公开诚实模型可达 ~8.1）。
- **CV 验证：** partial OOF fork（`joezzzzz/rogii-sunny-oof-codex`，FLAG_MODEL 模式，TEST_SIZE=120，GPU）运行中；
  报告 meta OOF CV = `<CV_PENDING>`（gate：显著 < DWT 10.40）。**即便 CV 未出，泄漏审计已决定性证明 Sunny 诚实。**
- **结论：能用 —— 作为诚实 slot 候选**（final-2 的诚实多样化第二槽；若 CV<10.40 且 fold 稳定，可作诚实 slot-1，
  DWT 作兜底 slot-2）。

## 3. deterministic DWT 是否替代 old DWT
- det-base **54775625 = 9.487**（`optuna n_jobs=1` 确定性、可复现，本分支 `rogii-dwt-detbase-codex`）vs old DWT
  **54453597 = 9.519**（`n_jobs=-1` 非确定性）。同模型/特征，仅后处理抽样不同；**私榜（诚实）行为基本相同**，0.032
  public 差为后处理噪声。
- **推荐：det-base 54775625 作为首选诚实 floor**（可复现 + 略优 public），old DWT 54453597 为等价 fallback。

## 4. honest meta/selector（备线 A）是否构建/提交
- **关闭（gate 未通过，未提交），理由：**
  1. **best-of-2 本身就是诚实 selector** —— 选 `{det-base DWT, Sunny}` 已在提交层实现"按私榜场景取 DWT 或 Sunny 中更优"。
     单一提交内的 blend/selector 需同时优于 DWT 和 Sunny 才有价值，门槛更高。
  2. 单提交内 blend **blend 中性**（20 轮证据；V3 pooled OOS 增益 −0.0024）；逐井 selector **不可辨识**（合成 selector
     16.32 > best-cost）。
  3. 唯一未测的希望（Sunny 强且去相关 → 正 blend）**不可负担地验证**：需全量 773 井 Sunny OOF 对齐 DWT，但 120 井
     partial 已跑 >30 分钟 → 全量不现实（数小时）；qwer 不可验证。
- **交付：honest meta = final-2 选择 `{det-base DWT, Sunny}`**（best-of-2 即 selector）。未做无证据的 blend 提交
  （遵守"没有足够证据不要为提交而提交"）。

## 5. final-2 三套推荐（备线 B）
诚实 floor = det-base DWT 54775625（old DWT 54453597 等价 fallback）。qwer/v36/spatial/B4′/DWT+affine 排除
（不可验证或被支配）。
- **novel-heavy（竞赛目标）：`{det-base DWT 54775625, Sunny PF90 54710185}`** —— overlap 对冲在新井无用；Sunny 诚实
  多样化，可能在新井超过 DWT；DWT 兜底。
- **overlap-heavy：`{det-base DWT 54775625, Gate-Safe 54289934}`** —— 诚实 floor + 经验证 affine overlay 对冲
  （7.212，唯一有真实边际的 overlap 玩法；v36/qwer 被支配）。
- **mixed/不确定：`{det-base DWT 54775625, Sunny PF90 54710185}`**（默认）—— 交叉点约 f≈0.4；因竞赛目标框定为新井
  （f 偏低），默认取 Sunny 诚实边际；若怀疑高 overlap 比例，则改用 `{DWT, Gate-Safe}`。

## 6. 明确关闭的方向 + 下一轮唯一最值得做
- **关闭：** qwer（不可验证/泄漏）、v36（无源/overlap）、spatial-formation（无源/部分 overlap）、naive DWT+affine
  （FP 不安全，+0.336 更差）、B4′ exact（无捕获）、单提交内 honest blend（被 best-of-2 支配 + blend 中性）。
- **下一轮唯一最值得做：** 取得**全量 Sunny OOF**（对齐 DWT 773 井）以做 DWT+Sunny **blend 权重检验** —— 这是唯一
  未验证的诚实杠杆（Sunny 强且可能去相关）。若正权重，则 DWT+Sunny blend 是更优单一诚实候选；若中性/负，则确认
  best-of-2 `{det-base DWT, Sunny}` 为最终诚实交付。（本轮因 partial 已 >30 分钟判定全量不现实而延后。）

## 7. 本轮提交说明
本轮**未新增竞赛提交**（final-2 = 选择既有已提交候选 det-base DWT 54775625 + Sunny 54710185；honest meta gate 未过）。
唯一 Kaggle 运行为 Sunny OOF 诊断 fork（非竞赛提交）。遵守"每次提交必须有明确目的、不做无解释扫射"——无明确增益的
候选不提交。（上轮已提交 det-base 54775625=9.487、DWT+affine 54775626=9.823。）
