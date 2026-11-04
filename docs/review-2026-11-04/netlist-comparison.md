# Full hierarchy pin comparison

Compare electrically equivalent groups by membership, ignoring labels and net codes.
Parts 123 → 123. Added [], removed [].
Declared pins 358 → 358. Added [], removed [].
Unchanged groups 129.
Each removed host bus group splits into two. This removes the direct powered-off path. No joined groups.

## Before
- /SDA_HOST — R20.1 U204.4 U205.1 U_BQ1.27
- /SCL_HOST — R21.1 U204.6 U205.2 U_BQ1.26
Declared pins absent from nets — none
All NC-typed pins — R124.2 R24.2 U204.3 U204.7 U_BQ1.19 U_BQ1.22 U_BQ1.34 U_BQ1.38 U_BQ1.39 U_BQ1.40 U_BQ1.43 U_BQ1.44 U_BQ1.45 U_BQ2.19 U_BQ2.22 U_BQ2.25 U_BQ2.34 U_BQ2.38 U_BQ2.39 U_BQ2.40 U_BQ2.43 U_BQ2.44 U_BQ2.45
Singletons (every member and classification)
- R24.2 — /Lower monitor/LD_WAKE_BQ1 — intentional NC / unresolved port
- U_BQ1.22 — /Lower monitor/TS2_WAKE_BQ1 — intentional NC / unresolved port
- U_BQ2.25 — /Upper I2C isolation/ALERT_BQ2 — intentional NC / unresolved port
- R124.2 — /Upper monitor/LD_WAKE_BQ2 — intentional NC / unresolved port
- U_BQ2.22 — /Upper monitor/TS2_WAKE_BQ2 — intentional NC / unresolved port
- R2.1 — CELL1 — external cell tap; harness absent
- R3.1 — CELL2 — external cell tap; harness absent
- R4.1 — CELL3 — external cell tap; harness absent
- R5.1 — CELL4 — external cell tap; harness absent
- R6.1 — CELL5 — external cell tap; harness absent
- R7.1 — CELL6 — external cell tap; harness absent
- R8.1 — CELL7 — external cell tap; harness absent
- R9.1 — CELL8 — external cell tap; harness absent
- R10.1 — CELL9 — external cell tap; harness absent
- R11.1 — CELL10 — external cell tap; harness absent
- R12.1 — CELL11 — external cell tap; harness absent
- R13.1 — CELL12 — external cell tap; harness absent
- R14.1 — CELL13 — external cell tap; harness absent
- R15.1 — CELL14 — external cell tap; harness absent
- R16.1 — CELL15 — external cell tap; harness absent
- R102.1 — CELL17 — external cell tap; harness absent
- R103.1 — CELL18 — external cell tap; harness absent
- R104.1 — CELL19 — external cell tap; harness absent
- R105.1 — CELL20 — external cell tap; harness absent
- R106.1 — CELL21 — external cell tap; harness absent
- R107.1 — CELL22 — external cell tap; harness absent
- R108.1 — CELL23 — external cell tap; harness absent
- R109.1 — CELL24 — external cell tap; harness absent
- R110.1 — CELL25 — external cell tap; harness absent
- R111.1 — CELL26 — external cell tap; harness absent
- R112.1 — CELL27 — external cell tap; harness absent
- R113.1 — CELL28 — external cell tap; harness absent
- R114.1 — CELL29 — external cell tap; harness absent
- R115.1 — CELL30 — external cell tap; harness absent
- R116.1 — CELL31 — external cell tap; harness absent
- U204.3 — unconnected-(U204-A2-Pad3) — intentional NC / unresolved port
- U204.7 — unconnected-(U204-B1-Pad7) — intentional NC / unresolved port
- U_BQ1.45 — unconnected-(U_BQ1-CHG-Pad45) — intentional NC / unresolved port
- U_BQ1.43 — unconnected-(U_BQ1-DSG-Pad43) — intentional NC / unresolved port
- U_BQ1.38 — unconnected-(U_BQ1-FUSE-Pad38) — intentional NC / unresolved port
- U_BQ1.19 — unconnected-(U_BQ1-NC-Pad19) — intentional NC / unresolved port
- U_BQ1.44 — unconnected-(U_BQ1-NC-Pad44) — intentional NC / unresolved port
- U_BQ1.40 — unconnected-(U_BQ1-PCHG-Pad40) — intentional NC / unresolved port
- U_BQ1.39 — unconnected-(U_BQ1-PDSG-Pad39) — intentional NC / unresolved port
- U_BQ1.34 — unconnected-(U_BQ1-REG2-Pad34) — intentional NC / unresolved port
- U_BQ2.45 — unconnected-(U_BQ2-CHG-Pad45) — intentional NC / unresolved port
- U_BQ2.43 — unconnected-(U_BQ2-DSG-Pad43) — intentional NC / unresolved port
- U_BQ2.38 — unconnected-(U_BQ2-FUSE-Pad38) — intentional NC / unresolved port
- U_BQ2.19 — unconnected-(U_BQ2-NC-Pad19) — intentional NC / unresolved port
- U_BQ2.44 — unconnected-(U_BQ2-NC-Pad44) — intentional NC / unresolved port
- U_BQ2.40 — unconnected-(U_BQ2-PCHG-Pad40) — intentional NC / unresolved port
- U_BQ2.39 — unconnected-(U_BQ2-PDSG-Pad39) — intentional NC / unresolved port
- U_BQ2.34 — unconnected-(U_BQ2-REG2-Pad34) — intentional NC / unresolved port
## After
- /Lower monitor/SDA_BQ1 — R20.1 U_BQ1.27
- /Lower monitor/SCL_BQ1 — R21.1 U_BQ1.26
- /SDA_HOST — U204.4 U205.1
- /SCL_HOST — U204.6 U205.2
Declared pins absent from nets — none
All NC-typed pins — R124.2 R24.2 U204.3 U204.7 U_BQ1.19 U_BQ1.22 U_BQ1.34 U_BQ1.38 U_BQ1.39 U_BQ1.40 U_BQ1.43 U_BQ1.44 U_BQ1.45 U_BQ2.19 U_BQ2.22 U_BQ2.25 U_BQ2.34 U_BQ2.38 U_BQ2.39 U_BQ2.40 U_BQ2.43 U_BQ2.44 U_BQ2.45
Singletons (every member and classification)
- R24.2 — /Lower monitor/LD_WAKE_BQ1 — intentional NC / unresolved port
- U_BQ1.22 — /Lower monitor/TS2_WAKE_BQ1 — intentional NC / unresolved port
- U_BQ2.25 — /Upper I2C isolation/ALERT_BQ2 — intentional NC / unresolved port
- R124.2 — /Upper monitor/LD_WAKE_BQ2 — intentional NC / unresolved port
- U_BQ2.22 — /Upper monitor/TS2_WAKE_BQ2 — intentional NC / unresolved port
- R2.1 — CELL1 — external cell tap; harness absent
- R3.1 — CELL2 — external cell tap; harness absent
- R4.1 — CELL3 — external cell tap; harness absent
- R5.1 — CELL4 — external cell tap; harness absent
- R6.1 — CELL5 — external cell tap; harness absent
- R7.1 — CELL6 — external cell tap; harness absent
- R8.1 — CELL7 — external cell tap; harness absent
- R9.1 — CELL8 — external cell tap; harness absent
- R10.1 — CELL9 — external cell tap; harness absent
- R11.1 — CELL10 — external cell tap; harness absent
- R12.1 — CELL11 — external cell tap; harness absent
- R13.1 — CELL12 — external cell tap; harness absent
- R14.1 — CELL13 — external cell tap; harness absent
- R15.1 — CELL14 — external cell tap; harness absent
- R16.1 — CELL15 — external cell tap; harness absent
- R102.1 — CELL17 — external cell tap; harness absent
- R103.1 — CELL18 — external cell tap; harness absent
- R104.1 — CELL19 — external cell tap; harness absent
- R105.1 — CELL20 — external cell tap; harness absent
- R106.1 — CELL21 — external cell tap; harness absent
- R107.1 — CELL22 — external cell tap; harness absent
- R108.1 — CELL23 — external cell tap; harness absent
- R109.1 — CELL24 — external cell tap; harness absent
- R110.1 — CELL25 — external cell tap; harness absent
- R111.1 — CELL26 — external cell tap; harness absent
- R112.1 — CELL27 — external cell tap; harness absent
- R113.1 — CELL28 — external cell tap; harness absent
- R114.1 — CELL29 — external cell tap; harness absent
- R115.1 — CELL30 — external cell tap; harness absent
- R116.1 — CELL31 — external cell tap; harness absent
- U204.3 — unconnected-(U204-A2-Pad3) — intentional NC / unresolved port
- U204.7 — unconnected-(U204-B1-Pad7) — intentional NC / unresolved port
- U_BQ1.45 — unconnected-(U_BQ1-CHG-Pad45) — intentional NC / unresolved port
- U_BQ1.43 — unconnected-(U_BQ1-DSG-Pad43) — intentional NC / unresolved port
- U_BQ1.38 — unconnected-(U_BQ1-FUSE-Pad38) — intentional NC / unresolved port
- U_BQ1.19 — unconnected-(U_BQ1-NC-Pad19) — intentional NC / unresolved port
- U_BQ1.44 — unconnected-(U_BQ1-NC-Pad44) — intentional NC / unresolved port
- U_BQ1.40 — unconnected-(U_BQ1-PCHG-Pad40) — intentional NC / unresolved port
- U_BQ1.39 — unconnected-(U_BQ1-PDSG-Pad39) — intentional NC / unresolved port
- U_BQ1.34 — unconnected-(U_BQ1-REG2-Pad34) — intentional NC / unresolved port
- U_BQ2.45 — unconnected-(U_BQ2-CHG-Pad45) — intentional NC / unresolved port
- U_BQ2.43 — unconnected-(U_BQ2-DSG-Pad43) — intentional NC / unresolved port
- U_BQ2.38 — unconnected-(U_BQ2-FUSE-Pad38) — intentional NC / unresolved port
- U_BQ2.19 — unconnected-(U_BQ2-NC-Pad19) — intentional NC / unresolved port
- U_BQ2.44 — unconnected-(U_BQ2-NC-Pad44) — intentional NC / unresolved port
- U_BQ2.40 — unconnected-(U_BQ2-PCHG-Pad40) — intentional NC / unresolved port
- U_BQ2.39 — unconnected-(U_BQ2-PDSG-Pad39) — intentional NC / unresolved port
- U_BQ2.34 — unconnected-(U_BQ2-REG2-Pad34) — intentional NC / unresolved port
