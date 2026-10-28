# Pre-submit audit — L4_aniso_A50_W025_vs_deployed

- decision: **PASS**
- candidate: `/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/full_out/submission.csv`
- baseline: `/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/dep_out/submission.csv`
- rows: 14151 (sample 14151), same_set=True, same_order=True
- finite: non-finite=0
- range: [11593.613904323996, 12243.216354793529] mean=11903.861613336583 out-of-band=0
- diff-vs-DWT: rmse=2.051 max|Δ|=7.94 %changed=100.0
- visible-well pooled RMSE: **3.4961**
    - 000d7d20: n=3836 RMSE=2.6497
    - 00bbac68: n=6014 RMSE=3.5212
    - 00e12e8b: n=4301 RMSE=4.0762
