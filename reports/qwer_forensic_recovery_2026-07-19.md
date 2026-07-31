# ROGII — qwer (54777533) forensic recovery (Direction E, 2026-07-19)

Session `1a07ce3e`. Exhaustive attempt to recover qwer's predictions or source. Neutral technical language.

## Search performed (this round)
| target | scope | result |
|---|---|---|
| `qwer` / `SHA424e` / `6.909` | `git log --all` | only the prior downgrade commit 783fdb6; no source commit |
| `qwer` / `sha424e` | `/home/ubuntu/.claude/jobs/**`, `/home/ubuntu/.codex/**` | hits ONLY in this session-chain's own state/timeline JSONL (my own qwer discussion); NOT in Codex rollouts |
| `qwer` / `424e` / `54777533` / `6.909` | `~/.bash_history` | no hits |
| submission-CSV backups | `find .../jobs .../JoeProject -name "submission*.csv"` | fleongg / baidalin / sp45 / gr_typewell artifacts only — none is qwer |
| kaggle output cache / dirs named qwer | `/home/ubuntu` maxdepth 5 | none |
| Kaggle API past-submission download | `competitions submissions --help` | no download option (only list/format) |
| kernel behind the 07:15 submit | joezzzzz kernel run-times | no kernel ran at 07:15; candidate kernels (neural-aligner/kokinn-v14/mycarta) carry no qwer/424e signature |

## Verdict — NOT recoverable (4th independent confirmation)
qwer's source and prediction vector are unrecoverable (remote Codex session, no local trace; SHA424e resolves
to nothing). Its error-correlation vs DWT+PF cannot be computed directly. **The honest-frontier argument stands
without it:** qwer's claimed OOF 6.909 is 2.39 (26%) below the verified honest frontier (DWT+PF 9.30) → it can
only fold overlap/train-duplicate leakage into the OOF; and its OOF→public direction (6.909→7.921, public
WORSE) is the overlap-overfit signature. **qwer is not honest and does not enter the final-2** (dominated by
Gate-Safe for the overlap slot; not honest for the honest slot). Detail: `qwer_final2_audit_2026-07-19.md`.
