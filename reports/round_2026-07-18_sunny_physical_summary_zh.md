# ROGII 2026-07-18 — Sunny 物理/PF 诚实 OOF 隔离 + DWT+PF 诚实 blend 中文总结（会话 06dd2efb）

链路：`16baec36 → dacc2829 → b2229931 → 99fff121 → 276bd506 → 06dd2efb`。用词中性技术性。

## 续（同会话，Kaggle smoke+submit 链路完成）— DWT+PF blend 已提交并公榜验证
- **Kaggle smoke 通过**：kernel `joezzzzz/rogii-dwt-pf-blend-codex` v1 push 后 interactive 运行（3 可见井）
  COMPLETE、0 error、日志含 `[PF-blend]` 执行证据、PF 覆盖 100%；submission.csv 行数/id 序/finite/range 全过；
  执行日志 grep 无 `tvt_from_contacts`/EGFDU/泄漏项。pre-submit 审计通过。
- **正式提交**（code-comp kernel submission）：**ref 54804893 → PUBLIC 8.080**。
- **迁移已验证并略微放大**：blend 公榜 8.080 vs DWT 9.487 = **+1.41（14.9%）**，大于 OOF 增益（+1.10 / 10.6%）；
  同时**优于 Sunny PF90（8.864）**。诚实模型（无 overlap 利用）在公榜上同时胜过诚实基线与被 overlap 泄漏抬升的
  Sunny → 去相关增益是真实、可迁移的，非本地 OOF 假象。私榜隐藏至 2026-08-05（OOF 9.30 为其代理）。
- **final-2 更新（已验证）**：**`{DWT+PF blend 54804893（public 8.080, OOF 9.30，最强诚实，取代 DWT 与 Sunny 的
  诚实槽）, Gate-Safe 54289934（public 7.212，overlap 兜底）}`**。取代原 `{DWT, Sunny PF90}` 与 `{DWT, Gate-Safe}`。
- **次线 Lucifer PF-stack 关闭（诚实负结果）**：15 井去相关复核（75,083 行，代表性：DWT 9.90≈全局 10.40）显示其额外
  诚实 forward（beam-DP 14.30/corrDWT 0.68、ANCC-PF 13.73/corrPF 0.67、Z-PF 17.83/corrDWT 0.49）均**弱于** DWT/plain-PF
  且**部分相关** → blend-中性，不提供超出已入列 DWT+PF blend 的去相关信号。不做全量 OOF、不提交。extract
  `scripts/lucifer_honest_forward.py`，报告 `lucifer_pf_stack_oof_plan_2026-07-18.md`。
- 报告：`dwt_pf_blend_kaggle_submit_2026-07-18.md`。本节以下为 OOF 隔离原始总结（保留）。

## 0. 是否有 agent/process 冲突
无。本会话 06dd2efb 为当前主延续；未发现其它 ROGII agent 处于 working。计算集中在一个本地后台 OOF 作业。

## 1. 当前是否有任务在跑
无。本地 PF-forward OOF 全量作业（773 井）已 **COMPLETE**（COMPLETE 后续无常驻任务）。次线的“其它诚实管线扫描”
子代理亦已完成。

## 2. Source mapping（A）
- 提交的 **Sunny PF90 beam-mean10（54710185, public 8.864）** 的物理组件 = `SUNNY_CODE`（338 行纯 CPU），
  嵌入并 exec 于 henry 笔记本 cell 108，产出 `submission_sunny_physical.csv`；henry final = 0.80·physical + 0.20·v10。
- 预测逻辑（主循环 L283-331）：**novel 井 → 诚实 PF forward `run_pf_lik_ensemble(hw,tw)`**（仅用 heel + typewell，
  测试可得输入）；**train/overlap 井（`if wid in train_wids`）→ `tvt_from_contacts`（泄漏）**。
- **泄漏订正（重要）：** `tvt_from_contacts` 用 `hw_tr['TVT']`（toe 真值）+ `hw_tr['EGFDU']`（train-only 结构面）。
  已用真实 schema 核实：**test 井仅有 MD,X,Y,Z,GR,TVT_input 六列**，TVT/EGFDU 均 train-only、test 不可得。故它
  只在 overlap 井触发、把 toe 重建到 ~0.007ft。**结论：Sunny GBM-meta（10.4732，上一轮）与物理 PF 是两个组件；
  8.864 的物理组件在 novel 井上就是诚实 PF forward，其 OOF 本轮已单独隔离。**

## 3. smoke（B，遵守 Directive 4）
- 首个单发 773 井 / n_seeds=32 作业 ~14min 后被资源回收、无 checkpoint、stdout 未捕获 → **重构** OOF harness：
  每 16 井 checkpoint、写可 tail 的进度日志、可 resume、确定性洗牌（部分结果即代表性）。
- 新 harness **smoke（3 随机 train 井 / n_seeds=8）PASS**：checkpoint 落盘、日志、running CV 均正常，输出有限、量纲合理。
- **blend notebook 本地 smoke PASS**：mock DWT + 真 PF（3 可见井）跑通 blend cell，14151 行、PF 覆盖 100%、全有限、
  id 集合与 sample_submission 一致、`blend==0.5·DWT+0.5·PF` 精确、TVT 量纲合理。

## 4. formal run 状态与结果（C）
- **诚实 PF-forward OOF：773 井 / 3,783,989 toe 行，n_seeds=24，本地 57min，COMPLETE。**
- **PF-forward 诚实 OOF pooled CV = 10.9952**（vs DWT native-mask 10.3987）→ **PF 单独比 DWT 略弱 ~0.6ft（pooled）**；
  但 **PF 中位井 5.65 < DWT 中位井 6.41**——PF 在“典型井”上更好，pooled 落后来自高漂移长井尾部。
- **误差相关 corr(err_DWT, err_PF) = 0.511**（去相关；对比 GBM blend 的 0.746）。
- **互补性（稳定）：** 易井 DWT 3.28 / PF 5.39（PF<DWT 32%）；难井 DWT 14.16 / **PF 11.20（PF<DWT 67%）**——
  PF 系统性救回 DWT 吃力的高漂移井。Oracle 逐井 selector = 7.56（上界，不可部署，需真值路由）。
- **DWT + PF 0.5/0.5 blend 诚实 OOF = 9.2969（相对 DWT 10.3987 增益 +1.10ft / 10.6%）。** 嵌套 2 折 a=0.40/0.48
  （两折稳定），**逐井 bootstrap 100% 为正 / 5th-pct +0.66**（从 272 井的 +0.09 收紧到 773 井的 +0.66）。
- **迁移稳健性：增益由“去相关”驱动，非“偏差抵消”**（加截距仅改变 −0.018ft；两模型近无偏 DWT −0.04 / PF −0.69）
  → 纯方差缩减、可迁移，非被公榜反复否定的负权重 λ-伪装。**这是项目至今最强的诚实信号（vs GBM blend +0.076）。**

## 5. 本轮提交与分数（D）
- **本轮未新增竞赛提交。** 原因：**本后台环境无 kaggle CLI / 凭据 / KAGGLE 变量**（全盘搜索为空），无法 push/submit。
- 已产出 **可提交且本地验证通过的 notebook**：`kaggle_kernel_dwt_pf_blend/`（banked det-base DWT + 一段诚实 PF-blend
  cell：NS=64、无 `tvt_from_contacts`、按 `id` 做 0.5·DWT+0.5·PF）。**pre-submit 审计通过**：仅用测试可得输入
  （grep 无 tvt_from_contacts/EGFDU/Geology/hw['TVT']）、格式/有限/id 序/量纲全过、权重固定不在测试端调参。
- **交接命令（用户在有凭据的会话执行；interactive 运行=3 可见井 smoke（Directive 4）；Submit=隐藏 rerun）：**
  ```
  kaggle kernels push -p kaggle_kernel_dwt_pf_blend
  kaggle kernels status  joezzzzz/rogii-dwt-pf-blend-codex     # 读 [PF-blend] 日志行
  kaggle kernels output  joezzzzz/rogii-dwt-pf-blend-codex -p /tmp/blendout   # 校验 submission.csv
  # smoke 日志 + 输出校验通过后，再在该 kernel 页面 Submit to Competition
  ```

## 6. final-2 是否变化（D）
- **是，建议更新。** 公榜=3 可见 overlap 井（泄漏博弈），私榜=隐藏 novel 井（奖项目标）；诚实 OOF 是唯一 novel 代理。
  - Sunny PF90 的 public 8.864 = overlap 泄漏（`0.80·leaked + 0.20·v10`），**不是 novel 强度**；novel 上 Sunny=诚实
    PF≈11.0≈DWT，**并非对 DWT 的提升**。
  - **DWT+PF blend 诚实 OOF 9.30（+1.10）= 目前最强诚实 novel 模型，支配 Sunny PF90 作为诚实第 2 槽。**
- **推荐（best-of-2，novel 目标）：`{det-base DWT 54775625（9.487，诚实兜底）, DWT+PF blend（诚实上行，提交并核对迁移）}`**
  （替换原 `{DWT, Sunny PF90}`；DWT 兜底 blend 的迁移风险，blend 为纯上行）。若担心私榜含 overlap，可用
  `{DWT+PF blend, Gate-Safe 7.212}` 兼顾 novel + overlap（代价是让出 DWT 兜底）。
- **诚实保留项：** blend 的公/私迁移**尚未验证**（本环境不能提交）；增益是“去相关”型（较可迁移），但仍需在提交时用
  smoke + Submit 核对。

## 7. 次线：其它诚实物理/序列/对齐管线扫描（已完成，已核实）
- **Lucifer `kaggle_kernel_lucifer_wellbore_wizard_pf_stack` 是 Sunny PF 的超集**（已 grep 核实）：含
  `beam_search`（beam-DP 对齐）、`run_pf_ancc`、`run_pf_z`、`run_pf_lik_ensemble`（同 Sunny）、`multi_scale_ncc`
  + `selector_well`，全部诚实、可逐井 masked-replay OOF、纯 CPU；泄漏仅限 overlap-only 的 `guarded_contact_override`
  （`if wid not in train_wells: continue`）。**下一轮最值得隔离的诚实新增信号**（Sunny 未出的 beam/ANCC-PF/Z-PF/NCC
  + selector，可能提供更多去相关分量）。
- 自足诚实原型：`scratchpad_probes/tw_align_proto.py`（typewell DTW warp，自足）、`bayesian_state_space_probe.py`
  （粒子平滑器）等。SSL/facies 编码器仓内标注对 DWT 为负权。**无 graph/GNN 模型**。
- 排除：`dip_probe.py` 用结构面作特征（train-only 泄漏，非可部署）。

## 8. 下一步唯一最值得做
**用户在有凭据会话 push `kaggle_kernel_dwt_pf_blend`（=3 井 smoke）→ 校验 → Submit（隐藏 rerun）→ 核对 public/private，**
以验证 DWT+PF blend（诚实 OOF 9.30）迁移；若迁移，即为最强诚实 novel 槽，落实 `{det-base DWT, DWT+PF blend}`。
其后可隔离 Lucifer 超集的 beam/ANCC-PF/Z-PF/NCC + selector 以叠加更多去相关诚实分量。
