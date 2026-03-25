"""
Family Ranking — Selects Dominant Pattern
==========================================

After family detectors run, this engine:
1. Collects all candidates from all families
2. Ranks them by confidence
3. Resolves conflicts
4. Returns dominant + alternatives

KEY PRINCIPLE: Better to return "no pattern" than garbage fallback
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from .pattern_family_matrix import PatternFamily, PatternBias


@dataclass
class RankedPattern:
    """A pattern with ranking metadata."""
    type: str
    family: PatternFamily
    bias: PatternBias
    confidence: float
    rank: int
    pattern_data: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "family": self.family.value,
            "bias": self.bias.value,
            "confidence": round(self.confidence, 2),
            "rank": self.rank,
            **self.pattern_data,
        }


@dataclass
class RankingResult:
    """Result of pattern ranking."""
    dominant: Optional[RankedPattern]
    alternatives: List[RankedPattern]
    rejected: List[Dict]  # Patterns below threshold with reasons
    conflict: Optional[str]  # If there's bullish/bearish conflict
    tradeable: bool
    
    def to_dict(self) -> Dict:
        return {
            "dominant": self.dominant.to_dict() if self.dominant else None,
            "alternatives": [a.to_dict() for a in self.alternatives],
            "rejected_count": len(self.rejected),
            "rejected": self.rejected[:3],  # Only first 3 for brevity
            "conflict": self.conflict,
            "tradeable": self.tradeable,
        }


class FamilyRanking:
    """
    Ranks and selects patterns from all families.
    
    Config:
    - min_confidence: minimum confidence to be considered
    - conflict_threshold: confidence difference to declare conflict
    - max_alternatives: how many alternatives to return
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        
        self.min_confidence = config.get("min_confidence", 0.4)
        self.conflict_threshold = config.get("conflict_threshold", 0.15)
        self.max_alternatives = config.get("max_alternatives", 2)
    
    def rank(
        self,
        candidates: List[Dict],  # Pattern dicts from family detectors
    ) -> RankingResult:
        """
        Rank all pattern candidates.
        
        Args:
            candidates: List of pattern dicts, each must have:
                - type: pattern name
                - family: family name
                - bias: bullish/bearish/neutral
                - confidence: 0-1
        
        Returns:
            RankingResult with dominant, alternatives, rejected
        """
        if not candidates:
            return RankingResult(
                dominant=None,
                alternatives=[],
                rejected=[],
                conflict=None,
                tradeable=False,
            )
        
        # Filter by minimum confidence
        valid = []
        rejected = []
        
        for c in candidates:
            conf = c.get("confidence", 0)
            if conf >= self.min_confidence:
                valid.append(c)
            else:
                rejected.append({
                    "type": c.get("type"),
                    "confidence": conf,
                    "reason": f"below_threshold ({conf:.2f} < {self.min_confidence})"
                })
        
        if not valid:
            return RankingResult(
                dominant=None,
                alternatives=[],
                rejected=rejected,
                conflict=None,
                tradeable=False,
            )
        
        # Sort by confidence
        valid.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        # Check for conflicts
        conflict = self._detect_conflict(valid)
        
        # Build ranked patterns
        ranked = []
        for i, c in enumerate(valid):
            ranked.append(RankedPattern(
                type=c.get("type"),
                family=PatternFamily(c.get("family", "horizontal")),
                bias=PatternBias(c.get("bias", "neutral")),
                confidence=c.get("confidence", 0),
                rank=i + 1,
                pattern_data=c,
            ))
        
        # Dominant is first (highest confidence)
        dominant = ranked[0] if ranked else None
        
        # Alternatives are next N
        alternatives = ranked[1:self.max_alternatives + 1] if len(ranked) > 1 else []
        
        # Tradeable if no conflict or dominant is clearly stronger
        tradeable = self._is_tradeable(dominant, alternatives, conflict)
        
        return RankingResult(
            dominant=dominant,
            alternatives=alternatives,
            rejected=rejected,
            conflict=conflict,
            tradeable=tradeable,
        )
    
    def _detect_conflict(self, patterns: List[Dict]) -> Optional[str]:
        """Detect if there's a bullish/bearish conflict."""
        if len(patterns) < 2:
            return None
        
        top_two = patterns[:2]
        bias1 = top_two[0].get("bias", "neutral")
        bias2 = top_two[1].get("bias", "neutral")
        
        # Both neutral = no conflict
        if bias1 == "neutral" or bias2 == "neutral":
            return None
        
        # Same bias = no conflict
        if bias1 == bias2:
            return None
        
        # Different biases
        conf1 = top_two[0].get("confidence", 0)
        conf2 = top_two[1].get("confidence", 0)
        
        # If confidence difference is small, it's a conflict
        if conf1 - conf2 < self.conflict_threshold:
            return f"bullish_bearish_conflict: {top_two[0].get('type')} ({bias1}) vs {top_two[1].get('type')} ({bias2})"
        
        return None
    
    def _is_tradeable(
        self,
        dominant: Optional[RankedPattern],
        alternatives: List[RankedPattern],
        conflict: Optional[str]
    ) -> bool:
        """Determine if the pattern setup is tradeable."""
        if not dominant:
            return False
        
        # Conflict = not tradeable
        if conflict:
            return False
        
        # Neutral bias with no directional alternative = not immediately tradeable
        if dominant.bias == PatternBias.NEUTRAL:
            # But if it's a breakout pattern (triangle, range), it could be tradeable at breakout
            return dominant.confidence >= 0.6
        
        # Clear directional bias with good confidence = tradeable
        return dominant.confidence >= self.min_confidence


# Singleton
_family_ranking = None

def get_family_ranking(config: Dict = None) -> FamilyRanking:
    global _family_ranking
    if _family_ranking is None or config:
        _family_ranking = FamilyRanking(config)
    return _family_ranking
