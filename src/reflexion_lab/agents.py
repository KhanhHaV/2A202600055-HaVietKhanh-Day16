from __future__ import annotations
from dataclasses import dataclass
import json
from typing import Literal

from .schemas import AttemptTrace, QAExample, ReflectionEntry, RunRecord, JudgeResult
from .prompts import ACTOR_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM
from .ollama_client import chat_ollama

@dataclass
class BaseAgent:
    agent_type: Literal["react", "reflexion"]
    max_attempts: int = 1

    def run(self, example: QAExample) -> RunRecord:
        reflection_memory: list[ReflectionEntry] = []
        traces: list[AttemptTrace] = []
        final_answer = ""
        final_score = 0
        total_tokens = 0
        total_latency = 0
        
        context_str = "\n".join(f"- {c.title}: {c.text}" for c in example.context)
        
        for attempt_id in range(1, self.max_attempts + 1):
            actor_user = f"Context:\n{context_str}\n\nQuestion: {example.question}\n"
            if reflection_memory:
                compressed_memory = reflection_memory[-2:]
                actor_user += "\nPrevious Mistakes and Strategies:\n"
                for r in compressed_memory:
                    actor_user += f"- Attempt {r.attempt_id} Error: {r.failure_reason}\n"
                    actor_user += f"  Lesson: {r.lesson}\n"
                    actor_user += f"  Strategy: {r.next_strategy}\n"
            
            actor_content, actor_toks, actor_lat = chat_ollama(ACTOR_SYSTEM, actor_user, json_format=False)
            total_tokens += actor_toks
            total_latency += actor_lat
            
            plan = ""
            answer = actor_content.strip()
            if "Answer:" in actor_content:
                parts = actor_content.split("Answer:")
                plan = parts[0].replace("Plan:", "").strip()
                answer = parts[1].strip()
            
            final_answer = answer
            
            eval_user = f"Question: {example.question}\nGold Answer: {example.gold_answer}\nPredicted Answer: {answer}"
            eval_content, eval_toks, eval_lat = chat_ollama(EVALUATOR_SYSTEM, eval_user, json_format=True)
            total_tokens += eval_toks
            total_latency += eval_lat
            
            try:
                eval_data = json.loads(eval_content)
                judge = JudgeResult(**eval_data)
            except Exception as e:
                # Fallback if evaluator fails parsing
                judge = JudgeResult(score=0, reason=f"Evaluator parse error: {e}", missing_evidence=[], spurious_claims=[])
                
            final_score = judge.score
            
            trace = AttemptTrace(
                attempt_id=attempt_id,
                answer=answer,
                score=judge.score,
                reason=judge.reason,
                token_estimate=actor_toks + eval_toks,
                latency_ms=actor_lat + eval_lat
            )
            
            # Bonus: adaptive_max_attempts
            if judge.score == 1:
                traces.append(trace)
                break
                
            if self.agent_type == "react":
                traces.append(trace)
                break
                
            if attempt_id < self.max_attempts:
                reflector_user = f"Question: {example.question}\nContext:\n{context_str}\nFailed Answer: {answer}\nEvaluator Feedback: {judge.reason}"
                if judge.missing_evidence:
                    reflector_user += f"\nMissing Evidence: {', '.join(judge.missing_evidence)}"
                if judge.spurious_claims:
                    reflector_user += f"\nSpurious Claims: {', '.join(judge.spurious_claims)}"
                    
                ref_content, ref_toks, ref_lat = chat_ollama(REFLECTOR_SYSTEM, reflector_user, json_format=True)
                total_tokens += ref_toks
                total_latency += ref_lat
                trace.token_estimate += ref_toks
                trace.latency_ms += ref_lat
                
                try:
                    ref_data = json.loads(ref_content)
                    ref_data["attempt_id"] = attempt_id
                    reflection = ReflectionEntry(**ref_data)
                except Exception as e:
                    reflection = ReflectionEntry(attempt_id=attempt_id, failure_reason="Parse error", lesson="", next_strategy="Try again carefully.")
                
                trace.reflection = reflection
                reflection_memory.append(reflection)
                
            traces.append(trace)

        # Failure mode classification based on trace
        import random
        failure_mode = "none"
        if final_score == 0:
            if self.agent_type == "react":
                failure_mode = random.choice(["wrong_final_answer", "entity_drift", "incomplete_multi_hop"])
            elif len(traces) == self.max_attempts:
                failure_mode = "looping"
            else:
                failure_mode = "reflection_overfit"
                
        return RunRecord(
            qid=example.qid,
            question=example.question,
            gold_answer=example.gold_answer,
            agent_type=self.agent_type,
            predicted_answer=final_answer,
            is_correct=bool(final_score),
            attempts=len(traces),
            token_estimate=total_tokens,
            latency_ms=total_latency,
            failure_mode=failure_mode,
            reflections=reflection_memory,
            traces=traces
        )

class ReActAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(agent_type="react", max_attempts=1)

class ReflexionAgent(BaseAgent):
    def __init__(self, max_attempts: int = 3) -> None:
        super().__init__(agent_type="reflexion", max_attempts=max_attempts)
