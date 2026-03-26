"""
Unified Pattern Detector V2
===========================

The SINGLE entry point for pattern detection.
Uses family architecture instead of 100 separate detectors.

Pipeline:
1. Find swings (once)
2. Classify into family
3. Run family detector(s)
4. Rank candidates
5. Return dominant + alternatives (or None)

KEY: Better to return None than garbage fallback!
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from .swing_engine import SwingEngine, SwingPoint, get_swing_engine
from .geometry_engine import GeometryEngine, get_geometry_engine
from .family_classifier import FamilyClassifier, ClassificationResult, get_family_classifier
from .family_ranking import FamilyRanking, RankingResult, get_family_ranking
from .pattern_family_matrix import PatternFamily
from .pattern_regime_binding import PatternRegimeBinder, get_pattern_regime_binder, RegimeContext
from .trigger_engine import TriggerEngine, get_trigger_engine, build_triggers

# Import family detectors
from .horizontal_family import HorizontalFamilyDetector, get_horizontal_family_detector
from .converging_family import ConvergingFamilyDetector, get_converging_family_detector


@dataclass
class DetectionResult:
    """Final result of pattern detection."""
    dominant: Optional[Dict]
    alternatives: List[Dict]
    family: Optional[str]
    classification: Dict
    ranking: Dict
    swings: Dict
    tradeable: bool
    confidence_state: str  # CLEAR / WEAK / CONFLICTED / COMPRESSION / NONE
    regime_context: Optional[Dict]  # Market regime info
    actionability: str     # HIGH / MEDIUM / LOW / NONE
    triggers: Optional[Dict]  # What to wait for
    
    def to_dict(self) -> Dict:
        return {
            "dominant": self.dominant,
            "alternatives": self.alternatives,
            "family": self.family,
            "classification": self.classification,
            "ranking": self.ranking,
            "swings": self.swings,
            "tradeable": self.tradeable,
            "confidence_state": self.confidence_state,
            "regime_context": self.regime_context,
            "actionability": self.actionability,
            "triggers": self.triggers,
        }


class UnifiedPatternDetectorV2:
    """
    The main pattern detector using family architecture.
    
    This replaces the old approach of running 100 detectors
    and falling back to loose_range.
    
    CRITICAL FIXES:
    - confidence = dominance, NOT pattern quality
    - NEVER 100% confidence
    - Regime binding for context
    - Triangle = compression, not signal
    
    Config:
    - run_all_families: True to run all families, False to run only classified
    - min_confidence: minimum to consider valid
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        
        self.run_all_families = config.get("run_all_families", True)
        self.min_confidence = config.get("min_confidence", 0.4)
        
        # Engines
        self.swing_engine = get_swing_engine(config.get("swing_config"))
        self.classifier = get_family_classifier(config)
        self.ranking = get_family_ranking(config)
        self.regime_binder = get_pattern_regime_binder(config)
        self.trigger_engine = get_trigger_engine(config)
        
        # Family detectors
        self.horizontal_detector = get_horizontal_family_detector(config.get("horizontal_config"))
        self.converging_detector = get_converging_family_detector(config.get("converging_config"))
    
    def detect(self, candles: List[Dict], structure: Dict = None, impulse: Dict = None) -> DetectionResult:
        """
        Detect patterns using family architecture with regime binding.
        
        Returns:
            DetectionResult with dominant pattern (or None)
        """
        if len(candles) < 20:
            return self._empty_result("insufficient_data")
        
        # 1. FIND SWINGS (once)
        swing_highs, swing_lows = self.swing_engine.find_swings(candles)
        
        swings_info = {
            "highs_count": len(swing_highs),
            "lows_count": len(swing_lows),
            "recent_highs": [h.to_dict() for h in swing_highs[-5:]],
            "recent_lows": [l.to_dict() for l in swing_lows[-5:]],
        }
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return self._empty_result("insufficient_swings", swings=swings_info)
        
        # 2. DETECT REGIME CONTEXT
        regime_context = self.regime_binder.detect_regime(structure, impulse, candles)
        
        # 3. CLASSIFY INTO FAMILY
        classification = self.classifier.classify(candles, swing_highs, swing_lows)
        
        # 4. RUN FAMILY DETECTORS
        all_candidates = []
        
        if self.run_all_families:
            all_candidates.extend(self._run_horizontal(candles, swing_highs, swing_lows))
            all_candidates.extend(self._run_converging(candles, swing_highs, swing_lows))
        else:
            if classification.primary_family:
                all_candidates.extend(self._run_family(
                    classification.primary_family, candles, swing_highs, swing_lows
                ))
                if classification.secondary_family:
                    all_candidates.extend(self._run_family(
                        classification.secondary_family, candles, swing_highs, swing_lows
                    ))
        
        # 5. APPLY REGIME BINDING
        bound_patterns = self.regime_binder.bind_all(all_candidates, regime_context)
        
        # Convert back to dicts with regime info
        bound_candidates = [bp.to_dict() for bp in bound_patterns]
        
        # 6. RANK CANDIDATES (with real confidence)
        ranking_result = self.ranking.rank(bound_candidates)
        
        # 7. DETERMINE CONFIDENCE STATE
        confidence_state = self._determine_confidence_state(ranking_result)
        
        # 8. GET ACTIONABILITY
        actionability = "NONE"
        if ranking_result.dominant:
            dom_data = ranking_result.dominant.pattern_data
            regime_binding = dom_data.get("regime_binding", {})
            actionability = regime_binding.get("actionability", "low").upper()
        
        # 9. BUILD TRIGGERS (what to wait for)
        triggers = None
        current_price = candles[-1].get("close", 0) if candles else 0
        
        if ranking_result.dominant:
            dom_data = ranking_result.dominant.pattern_data
            triggers = self.trigger_engine.build_triggers(
                dom_data, 
                current_price, 
                candles
            ).to_dict()
        
        # 10. BUILD RESULT
        dominant = None
        if ranking_result.dominant:
            dominant = ranking_result.dominant.to_dict()
        
        alternatives = [a.to_dict() for a in ranking_result.alternatives]
        
        return DetectionResult(
            dominant=dominant,
            alternatives=alternatives,
            family=classification.primary_family.value if classification.primary_family else None,
            classification=classification.to_dict(),
            ranking=ranking_result.to_dict(),
            swings=swings_info,
            tradeable=ranking_result.tradeable,
            confidence_state=confidence_state,
            regime_context=regime_context.to_dict(),
            actionability=actionability,
            triggers=triggers,
        )
    
    def _run_family(
        self,
        family: PatternFamily,
        candles: List[Dict],
        swing_highs: List[SwingPoint],
        swing_lows: List[SwingPoint]
    ) -> List[Dict]:
        """Run detector for a specific family."""
        if family == PatternFamily.HORIZONTAL:
            return self._run_horizontal(candles, swing_highs, swing_lows)
        elif family == PatternFamily.CONVERGING:
            return self._run_converging(candles, swing_highs, swing_lows)
        # TODO: Add other families
        return []
    
    def _run_horizontal(
        self,
        candles: List[Dict],
        swing_highs: List[SwingPoint],
        swing_lows: List[SwingPoint]
    ) -> List[Dict]:
        """Run horizontal family detector."""
        patterns = self.horizontal_detector.detect(candles, swing_highs, swing_lows)
        return [p.to_dict() for p in patterns]
    
    def _run_converging(
        self,
        candles: List[Dict],
        swing_highs: List[SwingPoint],
        swing_lows: List[SwingPoint]
    ) -> List[Dict]:
        """Run converging family detector."""
        patterns = self.converging_detector.detect(candles, swing_highs, swing_lows)
        return [p.to_dict() for p in patterns]
    
    def _determine_confidence_state(self, ranking: RankingResult) -> str:
        """
        Determine overall confidence state.
        
        CLEAR: Strong dominant pattern, no conflict, tradeable, directional
        WEAK: Pattern found but low confidence/dominance
        CONFLICTED: Bullish/bearish conflict or close competition
        COMPRESSION: Dominant is neutral (triangle/range) - wait for breakout
        NONE: No valid pattern
        """
        if not ranking.dominant:
            return "NONE"
        
        if ranking.conflict:
            return "CONFLICTED"
        
        # Check pattern type - neutral patterns = COMPRESSION
        dom_bias = ranking.dominant.bias
        if dom_bias == PatternBias.NEUTRAL:
            return "COMPRESSION"
        
        # Check dominance strength
        dom_conf = ranking.dominant.confidence
        
        if dom_conf >= 0.6 and ranking.tradeable:
            return "CLEAR"
        
        if dom_conf >= 0.4:
            return "WEAK"
        
        return "CONFLICTED"
    
    def _empty_result(
        self,
        reason: str,
        swings: Dict = None
    ) -> DetectionResult:
        """Return empty result with reason."""
        return DetectionResult(
            dominant=None,
            alternatives=[],
            family=None,
            classification={"reason": reason},
            ranking={"dominant": None, "alternatives": [], "rejected": []},
            swings=swings or {},
            tradeable=False,
            confidence_state="NONE",
            regime_context=None,
            actionability="NONE",
            triggers=None,
        )


# Singleton
_unified_detector = None

def get_unified_pattern_detector_v2(config: Dict = None) -> UnifiedPatternDetectorV2:
    global _unified_detector
    if _unified_detector is None or config:
        _unified_detector = UnifiedPatternDetectorV2(config)
    return _unified_detector


# ============================================================================
# INTEGRATION FUNCTION — Drop-in replacement for old detector
# ============================================================================

def detect_patterns_v2(candles: List[Dict], config: Dict = None) -> Dict:
    """
    Main entry point for pattern detection.
    
    Drop-in replacement for old pattern_detector.
    
    Returns:
        {
            "dominant": {...} or None,
            "alternatives": [...],
            "confidence_state": "CLEAR" / "WEAK" / "CONFLICTED" / "NONE",
            "tradeable": bool,
            ...
        }
    """
    detector = get_unified_pattern_detector_v2(config)
    result = detector.detect(candles)
    return result.to_dict()
