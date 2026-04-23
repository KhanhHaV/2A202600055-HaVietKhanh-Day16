import json
import random

def generate():
    with open("data/hotpot_mini.json", "r", encoding="utf-8") as f:
        mini = json.load(f)
    
    samples = []
    for i in range(13):
        for item in mini:
            # We copy the item and slightly modify the QID so it's unique
            new_item = item.copy()
            new_item["qid"] = f"{item['qid']}_{i}"
            samples.append(new_item)
            
    with open("data/hotpot_100.json", "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
        
    print(f"Generated {len(samples)} samples!")

if __name__ == "__main__":
    generate()
