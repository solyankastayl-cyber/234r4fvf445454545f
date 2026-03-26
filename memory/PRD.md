# TA Module — Product Requirements Document

## Original Problem Statement
Подними проект из репозитория https://github.com/solyankastayl-cyber/34444444, изучи архитектуру, подними bootstrap. Работаем только с модулем теханализа.

## Session Update: 2026-03-26
- Репозиторий клонирован и развёрнут
- Bootstrap выполнен: MongoDB + TA Engine + Exchange Intelligence
- Backend работает на localhost:8001
- Frontend скомпилирован на localhost:3000
- Pattern V2 API возвращает данные: BTC (triple_top), ETH (symmetrical_triangle)

### Pattern Window Validator Session
**Проблема:** Система рисовала triple_top там где его нет — паттерн был растянут на 80+ баров, не было uptrend'а перед ним, пики были на разных уровнях.

**Решение:** Pattern Window Validator с жёсткими проверками:
1. Window size — не больше 40 баров для 4H
2. Structural integrity — правильное количество пиков/впадин
3. Peak alignment — пики на одном уровне (±3.5%)
4. Depth check — минимальная глубина 2%
5. Pre-trend validation — uptrend перед top, downtrend перед bottom
6. Range conflict — пенализация если паттерн внутри активного range

**Результат:**
- BTC: triple_top ОТКЛОНЁН (no_uptrend_before_top: -11.3%)
- BTC: Теперь показывает rectangle вместо фейкового triple_top
- ETH: Все паттерны отклонены — показывает NONE (это правильно!)

**Файлы:**
- `pattern_window_validator.py` — новый валидатор
- `family_ranking.py` — интеграция валидатора
- `unified_detector.py` — передача candles/swings в валидатор
- `horizontal_family.py` — добавлены window и valleys

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

### Key Design Principles

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
   - Triangle in trend != triangle in chop
   - Actionability: HIGH/MEDIUM/LOW

4. **Trigger Engine**
   - What to WAIT for
   - Bullish triggers (breakout levels)
   - Bearish triggers (breakdown levels)
   - Invalidation levels

5. **Unified Render Contract**
   - One format for ALL patterns
   - Frontend just does: switch(render_mode) -> draw()
   - Modes: two_lines, polyline, box, hs

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

## What's Been Implemented

### Backend (DONE)
- Pattern Families architecture (6 families, 20+ patterns)
- Swing Engine (universal pivot detection)
- Geometry Engine (unified geometric rules)
- Real confidence calculation (dominance-based)
- Regime binding (context-aware scoring)
- Trigger Engine (wait conditions)
- Unified Render Contract
- API endpoint `/api/ta-engine/pattern-v2/{symbol}`

### Frontend V2 Integration (DONE - 2026-03-26)
- `usePatternV2` hook fetches V2 API data
- `patternRenderAdapter` normalizes backend response
- `PatternStateCard` renders decision-grade info below chart:
  - Pattern type + direction + state badge (CONFLICTED/CLEAR/COMPRESSION/WEAK)
  - Confidence, actionability, tradeable status
  - Wait Conditions: breakout/breakdown/invalidation trigger levels
  - Alternatives + regime context
- `PatternSVGOverlay` renders:
  - Pattern geometry (two_lines, polyline, box, hs modes)
  - Trigger lines (green breakout, red breakdown, orange invalidation)
- V2 render_contract passed to chart via data prop
- Legacy PatternOverlay hidden when V2 active
- Verified: BTC (Triple Top, CONFLICTED), ETH (Symmetrical Triangle, CONFLICTED)

## Testing Results

| Asset | Pattern | Confidence | State | Tradeable | Render Mode |
|-------|---------|------------|-------|-----------|-------------|
| ETH | symmetrical_triangle | 0.92 | CONFLICTED | No | two_lines |
| BTC | triple_top | 0.79 | CONFLICTED | No | polyline |

## Prioritized Backlog

### P0 (Critical - DONE)
- [x] Fix confidence calculation
- [x] Regime binding
- [x] Trigger engine
- [x] Unified render contract
- [x] Wire pattern-v2 to frontend (chart + triggers + state)

### P1 (Important - Next)
- [ ] Add parallel_family (channels, flags)
- [ ] Add swing_composite_family (H&S patterns)
- [ ] MTF Trigger Alignment (4H + 1D alignment)

### P2 (Nice to Have - Future)
- [ ] Trade Setup Generator (Entry, Stop, Targets, R:R) — only after V2 visual confirmed
- [ ] Execution Layer
- [ ] Backtesting integration

## Files of Reference

### Backend
- `/app/backend/modules/ta_engine/pattern_families/*` — V2 intelligence
- `/app/backend/modules/ta_engine/ta_routes.py` — API endpoints

### Frontend
- `/app/frontend/src/modules/ta/patterns/usePatternV2.js` — Data hook
- `/app/frontend/src/modules/ta/patterns/patternRenderAdapter.js` — Normalizer
- `/app/frontend/src/modules/ta/patterns/PatternStateCard.jsx` — UI card
- `/app/frontend/src/modules/cockpit/views/ResearchViewNew.jsx` — Main view
- `/app/frontend/src/modules/cockpit/components/PatternSVGOverlay.jsx` — Chart overlay
- `/app/frontend/src/modules/cockpit/components/ResearchChart.jsx` — Chart component
