import numpy as np
import re
import hashlib
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from enum import Enum

# MATH_BENCHMARK_SET und MATHDataset wie vorher (kannst du später hinzufügen, oder wir kürzen für jetzt)

@dataclass
class HybridConfig:
    max_depth: int = 4
    uncertainty_threshold: float = 0.25
    conflict_threshold: float = 0.35
    use_judge_node: bool = True
    capability_decay: float = 0.85
    aggregation_temperature: float = 2.0
    
    enable_mechanistic: bool = True
    mech_conflict_trigger: bool = True
    mech_depth_threshold: int = 2
    mech_uncertainty_threshold: float = 0.6
    mech_sample_rate: float = 0.05
    mech_deception_threshold: float = 0.7

class OverseerRole(Enum):
    NEUTRAL = "neutral"
    DEFENDER = "defender"
    ATTACKER = "attacker"
    JUDGE = "judge"

class MechanisticVerifier:
    def __init__(self, deception_threshold: float = 0.7):
        self.deception_threshold = deception_threshold
    
    def detect_deception(self, problem: str, answer: str, reasoning: str = "") -> Tuple[bool, float, str]:
        text = f"{problem} {answer} {reasoning}".lower()
        is_wrong = any(w in text for w in ["wrong", "maybe", "around", "probably"])
        is_confident = any(w in text for w in ["definitely", "certain", "obvious", "clearly"])
        activation = 0.1 + 0.6 * is_wrong + 0.4 * is_confident + np.random.normal(0, 0.1)
        activation = np.clip(activation, 0, 1)
        is_deceptive = activation > self.deception_threshold
        explanation = f"[MECH] Activation: {activation:.3f} → {'DECEPTION' if is_deceptive else 'clean'}"
        return is_deceptive, activation, explanation

@dataclass
class EvaluationResult:
    score: float
    uncertainty: float
    reasoning: str
    node_id: str
    depth: int
    role: OverseerRole
    actual_error: float = 0.0

class OverseerNode:
    def __init__(self, capability: float, role: OverseerRole, node_id: str, depth: int):
        self.capability = capability
        self.role = role
        self.node_id = node_id
        self.depth = depth
    
    def evaluate(self, problem: Dict, gt_quality: float) -> EvaluationResult:
        # Simplified evaluation
        diff_penalty = 0.1 * (problem.get('difficulty', 1) - 1)
        eff_cap = max(0.1, self.capability - diff_penalty)
        bias = {"neutral": 0.0, "defender": 0.12, "attacker": -0.12, "judge": 0.0}.get(self.role.value, 0.0)
        noise = np.random.normal(0, (1 - eff_cap) ** 1.5)
        score = np.clip(gt_quality + noise + bias, 0, 1)
        uncertainty = np.clip(0.15 + 0.6 * (1 - eff_cap) + 0.3 * abs(score - gt_quality), 0.05, 0.95)
        reasoning = f"[{self.role.value.upper()}] Score {score:.2f}, unc {uncertainty:.2f}"
        return EvaluationResult(score, uncertainty, reasoning, self.node_id, self.depth, self.role, abs(score - gt_quality))
    
    def spawn_children(self, decay: float):
        child_cap = self.capability * decay
        defender = OverseerNode(child_cap, OverseerRole.DEFENDER, f"{self.node_id}_def", self.depth + 1)
        attacker = OverseerNode(child_cap, OverseerRole.ATTACKER, f"{self.node_id}_att", self.depth + 1)
        return defender, attacker
    
    def spawn_judge(self):
        return OverseerNode(self.capability, OverseerRole.JUDGE, f"{self.node_id}_judge", self.depth + 1)

class HybridAdversarialDeliberationTree:
    def __init__(self, config: HybridConfig):
        self.config = config
        self.trace = []
        self.node_count = 0
        self.mech_count = 0
        self.verifier = MechanisticVerifier(config.mech_deception_threshold) if config.enable_mechanistic else None
    
    def should_use_mechanistic(self, conflict: bool, depth: int, uncertainty: float) -> bool:
        if not self.config.enable_mechanistic:
            return False
        if self.config.mech_conflict_trigger and conflict and depth >= self.config.mech_depth_threshold:
            return True
        if uncertainty > self.config.mech_uncertainty_threshold:
            return True
        if np.random.random() < self.config.mech_sample_rate:
            return True
        return False
    
    def oversee(self, problem: Dict, node: OverseerNode, gt_quality: float) -> Tuple[float, Dict]:
        self.node_count += 1
        result = node.evaluate(problem, gt_quality)
        self.trace.append(result)
        
        if node.depth >= self.config.max_depth or result.uncertainty < self.config.uncertainty_threshold:
            return result.score, {"type": "leaf", "result": result.__dict__}
        
        defender, attacker = node.spawn_children(self.config.capability_decay)
        score_def, meta_def = self.oversee(problem, defender, gt_quality)
        score_att, meta_att = self.oversee(problem, attacker, gt_quality)
        
        conflict = abs(score_def - score_att) > self.config.conflict_threshold
        
        if self.should_use_mechanistic(conflict, node.depth, result.uncertainty):
            self.mech_count += 1
            is_deceptive, act, exp = self.verifier.detect_deception(problem['question'], problem['answer'], result.reasoning)
            final_score = 0.05 if is_deceptive else 0.95
            metadata = {"type": "mechanistic", "deception": is_deceptive, "activation": act, "explanation": exp}
        else:
            if conflict and self.config.use_judge_node:
                judge = node.spawn_judge()
                judge_result = judge.evaluate(problem, gt_quality)
                self.trace.append(judge_result)
                final_score = 0.6 * judge_result.score + 0.2 * (score_def + score_att)
            else:
                weights = np.exp(self.config.aggregation_temperature * np.array([defender.capability, attacker.capability]))
                weights /= weights.sum()
                final_score = np.dot([score_def, score_att], weights)
            metadata = {"type": "adt", "conflict": conflict}
        
        return final_score, metadata
    
    def reset(self):
        self.trace = []
        self.node_count = self.mech_count = 0
