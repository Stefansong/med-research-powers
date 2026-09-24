#!/bin/sh
# Synthetic, clearly fake data for the eval — designed so that a good plan must react to the data:
#  * several rows per patient (one row per stone)       -> patient-level aggregation / GEE / mixed model
#  * disguised missing codes "未查" and "/"               -> recode to missing, handle in imputation plan
#  * censored lab strings like "<0.1"                     -> prespecified rule
#  * only ~30 recurrences for 12 candidate predictors     -> reduce predictors or penalise; Riley sample size
set -eu
cat > study-protocol.md <<'P'
# Study Protocol
type: clinical
title: 输尿管软镜碎石术后 2 年结石复发的预测模型（回顾性，单中心）
primary_outcome: 术后 2 年内影像学复发（recurrence_2y，0/1）
candidate_predictors: age, sex, bmi, diabetes, hypertension, stone_count, max_stone_mm, stone_location, hu_density, urine_ph, urine_citrate, serum_uric_acid
design: 回顾性队列，2018–2023 年行输尿管软镜碎石的患者
analysis_intent: 建立并内部验证临床预测模型，绘制列线图
P
python3 - <<'PY'
import random, csv
random.seed(7)
rows=[]
for pid in range(1, 401):
    n_stones = random.choice([1,1,1,2,2,3])
    rec = 1 if random.random() < 0.075 else 0          # ~30 events in 400 patients
    base = dict(patient_id=f"P{pid:04d}", age=random.randint(22,80), sex=random.choice(["男","女"]),
                bmi=round(random.uniform(18,34),1), diabetes=random.choice([0,0,0,1]),
                hypertension=random.choice([0,0,1]), urine_ph=round(random.uniform(5.0,7.5),1),
                serum_uric_acid=random.randint(200,520), recurrence_2y=rec)
    citrate = random.choice(["<0.1", str(round(random.uniform(0.1,4.0),2)), "未查", "/"])
    for s in range(n_stones):
        r = dict(base); r.update(stone_id=s+1, max_stone_mm=round(random.uniform(4,25),1),
                                 stone_location=random.choice(["上盏","中盏","下盏","肾盂"]),
                                 hu_density=random.choice([str(random.randint(300,1500)),"未查"]),
                                 urine_citrate=citrate)
        rows.append(r)
cols=["patient_id","stone_id","age","sex","bmi","diabetes","hypertension","max_stone_mm","stone_location",
      "hu_density","urine_ph","urine_citrate","serum_uric_acid","recurrence_2y"]
with open("data.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(rows)
PY
