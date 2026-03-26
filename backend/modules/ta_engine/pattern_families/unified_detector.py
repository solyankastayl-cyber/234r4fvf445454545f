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
from .pattern_family_matrix import PatternFamily, PatternBias
from .pattern_regime_binding import PatternRegimeBinder, get_pattern_regime_binder, RegimeContext
from .trigger_engine import TriggerEngine, get_trigger_engine, build_triggers
from .pattern_render_builder import build_render_contract
from .visual_mode_resolver import get_visual_mode_resolver, filter_render_for_mode

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
    render_contract: Optional[Dict]  # UNIFIED RENDER for frontend
    visual_mode: Optional[Dict] = None  # What frontend is ALLOWED to render
    
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
            "render_contract": self.render_contract,
            "visual_mode": self.visual_mode,
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
            "recent_lows": [sw.to_dict() for sw in swing_lows[-5:]],
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
        
        # 6. RANK CANDIDATES (with real confidence + WINDOW VALIDATION)
        # Convert swings to dicts for validator
        all_swings = []
        for high in swing_highs:
            all_swings.append({"index": high.index, "price": high.price, "type": high.type.value})
        for low in swing_lows:
            all_swings.append({"index": low.index, "price": low.price, "type": low.type.value})
        
        # Detect active range for conflict check
        active_range = self._detect_active_range(candles, swing_highs, swing_lows)
        
        # Get timeframe from candles metadata or default
        timeframe = candles[0].get("timeframe", "4H") if candles else "4H"
        
        ranking_result = self.ranking.rank(
            bound_candidates,
            candles=candles,
            swings=all_swings,
            active_range=active_range,
            timeframe=timeframe
        )
        
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
        
        # 10. BUILD RENDER CONTRACT (unified geometry for frontend)
        render_contract = None
        visual_mode = None
        dominant_type = None
        
        if ranking_result.dominant:
            dom_data = ranking_result.dominant.pattern_data
            dominant_type = dom_data.get("type")
            raw_render = build_render_contract(dom_data, None, candles)
            
            # 11. APPLY VISUAL MODE FILTER (CRITICAL!)
            # This strips out everything frontend is NOT allowed to render
            resolver = get_visual_mode_resolver()
            visual_mode = resolver.get_allowed_elements(dominant_type, confidence_state)
            render_contract = filter_render_for_mode(raw_render, dominant_type, confidence_state)
        else:
            # No dominant - show structure only mode
            resolver = get_visual_mode_resolver()
            visual_mode = resolver.get_allowed_elements(None, confidence_state)
        
        # 12. BUILD RESULT
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
            render_contract=render_contract,
            visual_mode=visual_mode,
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
            render_contract=None,
        )
    
    def _detect_active_range(
        self,
        candles: List[Dict],
        swing_highs: List[SwingPoint],
        swing_lows: List[SwingPoint]
    ) -> Optional[Dict]:
        """
        Detect if there's an active range.
        
        Used for:
        - Pattern conflict resolution
        - Window validation
        
        Returns:
            Range dict or None
        """
        if len(candles) < 20 or not swing_highs or not swing_lows:
            return None
        
        # Look at recent swings (last 30 bars)
        recent_range = 30
        recent_highs = [high for high in swing_highs if high.index >= len(candles) - recent_range]
        recent_lows = [low for low in swing_lows if low.index >= len(candles) - recent_range]
        
        if len(recent_highs) < 2 or len(recent_lows) < 2:
            return None
        
        # Check if highs and lows are roughly horizontal
        high_prices = [high.price for high in recent_highs]
        low_prices = [low.price for low in recent_lows]
        
        high_avg = sum(high_prices) / len(high_prices)
        low_avg = sum(low_prices) / len(low_prices)
        
        high_spread = (max(high_prices) - min(high_prices)) / high_avg if high_avg > 0 else 0
        low_spread = (max(low_prices) - min(low_prices)) / low_avg if low_avg > 0 else 0
        
        # If both spreads are small, we have a range
        if high_spread < 0.04 and low_spread < 0.04:  # < 4% spread
            return {
                "top": max(high_prices),
                "bottom": min(low_prices),
                "start_index": min(high.index for high in recent_highs),
                "end_index": len(candles) - 1,
                "touches_top": len(recent_highs),
                "touches_bottom": len(recent_lows),
            }
        
        return None


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
