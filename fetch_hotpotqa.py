import json
from datasets import load_dataset
import random

def fetch_data():
    print("Loading HotpotQA dataset (streaming mode)...")
    # Load the validation set using streaming to avoid downloading the huge dataset
    dataset = load_dataset("hotpot_qa", "distractor", split="validation", streaming=True)
    
    samples = []
    # Take first 100 samples from the stream
    for item in dataset.take(100):
        # Format context
        context_chunks = []
        for title, sentences in zip(item['context']['title'], item['context']['sentences']):
            context_chunks.append({
                "title": title,
                "text": " ".join(sentences)
            })
            
        samples.append({
            "qid": item['id'],
            "difficulty": item['level'],
            "question": item['question'],
            "gold_answer": item['answer'],
            "context": context_chunks
        })
        
    with open("data/hotpot_100.json", "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
        
    print(f"Saved {len(samples)} samples to data/hotpot_100.json")

if __name__ == "__main__":
    fetch_data()
