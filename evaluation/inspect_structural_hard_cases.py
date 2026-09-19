import json

PATH = "evaluation/structural_mapping_candidates.json"

TARGETS = {
    "Q021",
    "Q031",
    "Q040",
}

with open(PATH, encoding="utf-8") as f:
    data = json.load(f)

for q in data:
    if q["question_id"] not in TARGETS:
        continue

    print("\n" + "=" * 100)
    print(q["question_id"])
    print(q["question"])
    print("=" * 100)

    for item in q["evidence_items"]:
        print("\nEVIDENCE")
        print(item["evidence_text"])

        for c in item["candidates"]:
            print("\n" + "-" * 80)
            print(
                f"rank={c['rank']} "
                f"chunk_index={c['chunk_index']}"
            )
            print(
                f"chunk_id={c['chunk_id']}"
            )
            print("-" * 80)
            print(c["content"])
            