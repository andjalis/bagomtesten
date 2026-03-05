import json
import random
import os

os.makedirs("data/precomputed", exist_ok=True)
answers = []
for i in range(1, 501):
    ans_list = [random.randint(0, 3) for _ in range(25)]
    answers.append({
        "run_id": i,
        "answers_json": json.dumps(ans_list)
    })

with open("data/precomputed/answers_sample.json", "w") as f:
    json.dump(answers, f)

print("Created data/precomputed/answers_sample.json with 500 rows.")
