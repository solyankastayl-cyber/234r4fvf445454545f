"""
Pattern Lifecycle Engine - Track Pattern State
===============================================

Patterns are not static. They have a lifecycle:

1. FORMING - Pattern is building, price inside boundaries
2. MATURING - Pattern almost complete, nearing apex/resolution
3. CONFIRMED - Breakout happened in expected direction
4. BROKEN - Breakout failed or wrong direction
5. INVALIDATED - Pattern no longer relevant

This engine determines the current lifecycle stage.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class LifecycleResult:
    """Pattern lifecycle analysis result."""
    stage: str  # forming, maturing, confirmed, broken, invalidated
    completion: float  # 0.0 - 1.0
    breakout_status: str  # not_triggered, probing, confirmed, failed
    invalidation_status: str  # valid, weakened, invalid
    state_reason: str


class PatternLifecycleEngine:
    """
    Determines pattern lifecycle stage.
    
    Transforms static patterns into living entities.
    """
    
    # Completion thresholds
    MATURING_THRESHOLD = 0.75
    
    # Breakout detection
    BREAKOUT_THRESHOLD_PCT = 0.005  # 0.5% beyond boundary
    PROBING_THRESHOLD_PCT = 0.002  # 0.2% beyond boundary
    
    def __init__(self):
        pass
    
    def analyze(
        self,
        pattern: Dict,
        candles: List[Dict]
    ) -> LifecycleResult:
        """
        Analyze pattern lifecycle.
        
        Returns:
            LifecycleResult with stage and supporting data
        """
        if not pattern or not candles or len(candles) < 3:
            return LifecycleResult(
                stage="invalidated",
                completion=0.0,
                breakout_status="not_triggered",
                invalidation_status="invalid",
                state_reason="Insufficient data"
            )
        
        # Calculate metrics
        completion = self._compute_completion(pattern, candles)
        breakout_status = self._compute_breakout_status(pattern, candles)
        invalidation_status = self._compute_invalidation_status(pattern, candles)
        
        # Determine stage
        stage = self._determine_stage(completion, breakout_status, invalidation_status)
        
        # Build reason
        state_reason = self._build_state_reason(
            pattern, stage, breakout_status, invalidation_status, completion
        )
        
        return LifecycleResult(
            stage=stage,
            completion=round(completion, 2),
            breakout_status=breakout_status,
            invalidation_status=invalidation_status,
            state_reason=state_reason
        )
    
    def _compute_completion(self, pattern: Dict, candles: List[Dict]) -> float:
        """
        Compute how complete the pattern is.
        
        For wedge/triangle: distance to apex
        For channel: time elapsed in pattern
        """
        pattern_type = pattern.get("type", "")
        window = pattern.get("window", {})
        
        # Get pattern time range
        window_start = window.get("start_time", 0)
        window_end = window.get("end_time", 0)
        
        if window_start == 0 or window_end == 0:
            # Fall back to boundary times
            render = pattern.get("render", {})
            boundaries = render.get("boundaries", [])
            if boundaries:
                window_start = min(b.get("x1", 0) for b in boundaries)
                window_end = max(b.get("x2", 0) for b in boundaries)
        
        if window_start == 0 or window_end == 0:
            return 0.5  # Can't determine
        
        # Current time
        current_time = candles[-1].get("time", 0)
        
        if current_time <= window_start:
            return 0.0
        
        if current_time >= window_end:
            return 1.0
        
        # Linear completion based on time
        elapsed = current_time - window_start
        total = window_end - window_start
        
        if total <= 0:
            return 0.5
        
        return min(1.0, elapsed / total)
    
    def _compute_breakout_status(self, pattern: Dict, candles: List[Dict]) -> str:
        """
        Compute breakout status.
        
        Returns: not_triggered, probing, confirmed, failed
        """
        if len(candles) < 2:
            return "not_triggered"
        
        last_candle = candles[-1]
        prev_candle = candles[-2]
        
        last_close = last_candle.get("close", 0)
        last_high = last_candle.get("high", 0)
        last_low = last_candle.get("low", 0)
        prev_close = prev_candle.get("close", 0)
        
        current_time = last_candle.get("time", 0)
        
        # Get projected boundary values at current time
        upper_price = self._get_boundary_price(pattern, "upper", current_time)
        lower_price = self._get_boundary_price(pattern, "lower", current_time)
        
        if upper_price is None or lower_price is None:
            return "not_triggered"
        
        direction = pattern.get("direction", "neutral")
        
        # Bullish patterns: expect upside breakout
        if direction == "bullish":
            # Confirmed: close above upper + previous close above
            if last_close > upper_price * (1 + self.BREAKOUT_THRESHOLD_PCT):
                if prev_close > upper_price * (1 + self.PROBING_THRESHOLD_PCT):
                    return "confirmed"
                return "probing"
            
            # Probing: high above upper
            if last_high > upper_price:
                return "probing"
            
            # Failed: broke down instead
            if last_close < lower_price * (1 - self.BREAKOUT_THRESHOLD_PCT):
                return "failed"
        
        # Bearish patterns: expect downside breakout
        elif direction == "bearish":
            # Confirmed: close below lower + previous close below
            if last_close < lower_price * (1 - self.BREAKOUT_THRESHOLD_PCT):
                if prev_close < lower_price * (1 - self.PROBING_THRESHOLD_PCT):
                    return "confirmed"
                return "probing"
            
            # Probing: low below lower
            if last_low < lower_price:
                return "probing"
            
            # Failed: broke up instead
            if last_close > upper_price * (1 + self.BREAKOUT_THRESHOLD_PCT):
                return "failed"
        
        # Neutral patterns (symmetrical triangle): check both directions
        else:
            # Up breakout
            if last_close > upper_price * (1 + self.BREAKOUT_THRESHOLD_PCT):
                return "confirmed"
            if last_high > upper_price:
                return "probing"
            
            # Down breakout
            if last_close < lower_price * (1 - self.BREAKOUT_THRESHOLD_PCT):
                return "confirmed"
            if last_low < lower_price:
                return "probing"
        
        return "not_triggered"
    
    def _get_boundary_price(
        self,
        pattern: Dict,
        boundary_type: str,  # "upper" or "lower"
        at_time: int
    ) -> Optional[float]:
        """
        Get projected boundary price at a given time.
        
        Uses linear interpolation/extrapolation from boundary line.
        """
        render = pattern.get("render", {})
        boundaries = render.get("boundaries", [])
        
        target_boundary = None
        for b in boundaries:
            if boundary_type in b.get("id", "").lower():
                target_boundary = b
                break
        
        if not target_boundary:
            return None
        
        x1 = target_boundary.get("x1", 0)
        y1 = target_boundary.get("y1", 0)
        x2 = target_boundary.get("x2", 0)
        y2 = target_boundary.get("y2", 0)
        
        if x1 == x2:
            return y1  # Horizontal line
        
        # Linear interpolation/extrapolation
        slope = (y2 - y1) / (x2 - x1)
        price = y1 + slope * (at_time - x1)
        
        return price
    
    def _compute_invalidation_status(self, pattern: Dict, candles: List[Dict]) -> str:
        """
        Compute invalidation status.
        
        Returns: valid, weakened, invalid
        """
        if not candles:
            return "invalid"
        
        current_time = candles[-1].get("time", 0)
        current_price = candles[-1].get("close", 0)
        
        # Get pattern window
        window = pattern.get("window", {})
        window_end = window.get("end_time", 0)
        
        # Check if pattern is too old
        if window_end > 0:
            time_since_end = current_time - window_end
            # If more than 30 days past pattern end
            if time_since_end > 30 * 86400:
                return "invalid"
            # If more than 7 days past
            if time_since_end > 7 * 86400:
                return "weakened"
        
        # Check if price is too far from pattern
        upper = self._get_boundary_price(pattern, "upper", current_time)
        lower = self._get_boundary_price(pattern, "lower", current_time)
        
        if upper and lower:
            range_size = upper - lower
            if range_size > 0:
                # If price is more than 2x the range away
                if current_price > upper + range_size * 2:
                    return "invalid"
                if current_price < lower - range_size * 2:
                    return "invalid"
                # If more than 1x away
                if current_price > upper + range_size:
                    return "weakened"
                if current_price < lower - range_size:
                    return "weakened"
        
        return "valid"
    
    def _determine_stage(
        self,
        completion: float,
        breakout_status: str,
        invalidation_status: str
    ) -> str:
        """
        Determine lifecycle stage from metrics.
        """
        # Priority order
        if invalidation_status == "invalid":
            return "invalidated"
        
        if breakout_status == "confirmed":
            return "confirmed"
        
        if breakout_status == "failed":
            return "broken"
        
        if completion >= self.MATURING_THRESHOLD:
            return "maturing"
        
        return "forming"
    
    def _build_state_reason(
        self,
        pattern: Dict,
        stage: str,
        breakout_status: str,
        invalidation_status: str,
        completion: float
    ) -> str:
        """
        Build human-readable state reason.
        """
        pattern_type = pattern.get("type", "pattern")
        direction = pattern.get("direction", "neutral")
        
        reasons = {
            "forming": f"{pattern_type.replace('_', ' ').title()} is forming. "
                      f"Price contained within boundaries. {int(completion*100)}% complete.",
            
            "maturing": f"{pattern_type.replace('_', ' ').title()} approaching resolution. "
                       f"Watch for breakout in {direction} direction.",
            
            "confirmed": f"Breakout confirmed! {pattern_type.replace('_', ' ').title()} "
                        f"resolved in {direction} direction.",
            
            "broken": f"{pattern_type.replace('_', ' ').title()} failed. "
                     f"Price broke in wrong direction.",
            
            "invalidated": f"{pattern_type.replace('_', ' ').title()} no longer valid. "
                          f"Pattern expired or price moved too far.",
        }
        
        return reasons.get(stage, f"Pattern in {stage} stage.")


# Singleton
_lifecycle_engine = None

def get_pattern_lifecycle_engine() -> PatternLifecycleEngine:
    """Get pattern lifecycle engine singleton."""
    global _lifecycle_engine
    if _lifecycle_engine is None:
        _lifecycle_engine = PatternLifecycleEngine()
    return _lifecycle_engine
