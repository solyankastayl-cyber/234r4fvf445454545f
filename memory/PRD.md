# TA Module — Product Requirements Document

## Original Problem Statement
Подними проект из репозитория https://github.com/solyankastayl-cyber/frfr, изучи архитектуру, подними bootstrap. Работаем только с модулем теханализа.

## Architecture: Pattern Families System

### Core Components Created

```
/app/backend/modules/ta_engine/pattern_families/
├── __init__.py
├── swing_engine.py              # Universal swing point detection
├── geometry_engine.py           # Unified geometric rules
├── pattern_family_matrix.py     # All patterns by family (6 families)
├── horizontal_family.py         # double/triple top/bottom, range, rectangle
├── converging_family.py         # triangles, wedges
├── family_classifier.py         # Routes to correct family
├── family_ranking.py            # Ranks patterns, computes REAL confidence
├── pattern_regime_binding.py    # Context: pattern + market regime
├── trigger_engine.py            # What to WAIT for
├── pattern_render_builder.py    # UNIFIED render contract for frontend
└── unified_detector.py          # Main entry point
```

### Key Fixes Implemented

1. **Confidence = Dominance** (not pattern quality)
   - Never 100% (max 92%)
   - Based on gap between top patterns

2. **Confidence States**
   - CLEAR: Can trade
   - WEAK: Trade with caution
   - CONFLICTED: Don't trade
   - COMPRESSION: Wait for breakout
   - NONE: No pattern

3. **Regime Binding**
   - Pattern meaning changes by context
   - Triangle in trend ≠ triangle in chop
   - Actionability: HIGH/MEDIUM/LOW

4. **Trigger Engine**
   - What to WAIT for
   - ▲ Bullish triggers
   - ▼ Bearish triggers  
   - ✗ Invalidation levels

5. **Unified Render Contract**
   - One format for ALL patterns
   - Frontend just does: switch(type) → draw()

### API Endpoint

`GET /api/ta-engine/pattern-v2/{symbol}?timeframe=4H`

Returns:
- dominant pattern
- alternatives
- confidence_state
- tradeable
- actionability
- triggers
- render_contract
- regime_context

## What's Been Implemented (2026-03-26)

### Backend
- ✅ Pattern Families architecture (6 families, 20+ patterns)
- ✅ Swing Engine (universal pivot detection)
- ✅ Geometry Engine (unified geometric rules)
- ✅ Real confidence calculation (dominance-based)
- ✅ Regime binding (context-aware scoring)
- ✅ Trigger Engine (wait conditions)
- ✅ Unified Render Contract
- ✅ New API endpoint `/api/ta-engine/pattern-v2/{symbol}`

### Frontend
- ✅ PatternSVGOverlay updated with unified render functions
- ✅ Support for: box, polyline, two_lines, hs render modes

## Testing Results

| Asset | Pattern | Confidence | State | Tradeable |
|-------|---------|------------|-------|-----------|
| ETH | symmetrical_triangle | 0.92 | CONFLICTED | No |
| BTC | triple_top | 0.79 | CONFLICTED | No |

## Prioritized Backlog

### P0 (Critical - Done)
- ✅ Fix confidence calculation
- ✅ Regime binding
- ✅ Trigger engine
- ✅ Unified render contract

### P1 (Important)
- [ ] Integrate render_contract into existing frontend flow
- [ ] Add parallel_family (channels, flags)
- [ ] Add swing_composite_family (H&S patterns)
- [ ] MTF Trigger Alignment

### P2 (Nice to Have)
- [ ] Entry Engine (only when CLEAR)
- [ ] Execution Layer
- [ ] Backtesting integration

## Next Tasks
1. Wire new pattern-v2 API to ResearchViewNew.jsx
2. Test visual rendering on chart
3. Add remaining pattern families
