# TA Engine - Technical Analysis Module PRD

## Project Overview
Technical Analysis Engine with 10-layer decision system for crypto market analysis.

## Original Problem Statement
Развернуть проект из GitHub репозитория, изучить архитектуру и поднять модуль теханализа. Работа только с модулем TA Engine - 10-слойная система принятия решений. Критический фикс: frontend должен использовать ta_layers как источник истины, а не старый pattern_render_contract.

## Architecture - 10 Layer Decision System

### Layers:
1. **Market Structure** - HH/HL/LH/LL, trend direction, BOS/CHOCH
2. **Impulse & Context** - направление импульса, сила
3. **Volatility/Regime** - trend vs range vs compression
4. **Range Engine** - активный range как режим рынка (КРИТИЧЕСКИЙ)
5. **Pattern Detection** - double top, triangle, wedge, etc.
6. **Confluence Layer** - сколько факторов совпадает
7. **Probability Engine** - bullish/bearish probabilities
8. **Scenario Engine** - break up/down targets
9. **Timing Layer** - early/mid/late phase
10. **Narrative Engine** - человеческое объяснение

## Key Files
- `/app/backend/modules/ta_engine/ta_aggregator.py` - 10-layer aggregator
- `/app/backend/modules/ta_engine/impulse_engine.py` - Layer 2
- `/app/backend/modules/ta_engine/probability_engine.py` - Layer 7
- `/app/backend/modules/ta_engine/setup/range_regime_engine.py` - Layer 3+4
- `/app/backend/modules/ta_engine/per_tf_builder.py` - main pipeline
- `/app/frontend/src/modules/cockpit/components/PatternSVGOverlay.jsx` - SVG overlay (ПЕРЕПИСАН)
- `/app/frontend/src/modules/cockpit/components/ResearchChart.jsx` - chart component
- `/app/frontend/src/modules/cockpit/views/ResearchViewNew.jsx` - research view (ОБНОВЛЁН)
- `/app/frontend/src/modules/cockpit/components/TALayersPanel.jsx` - UI component

## Tech Stack
- **Backend**: Python, FastAPI, MongoDB
- **Frontend**: React, styled-components, lightweight-charts
- **Data**: Coinbase API for real-time prices

## What's Implemented (March 2026)

### Session 1 - Project Setup
- [x] Cloned repository from GitHub
- [x] Bootstrap completed (BTC, ETH, SOL, SPX, DXY data loaded)
- [x] Backend running on port 8001
- [x] Frontend running on port 3000

### Session 2 - TA Layers Integration (CRITICAL FIX)
- [x] **FIXED**: PatternSVGOverlay теперь использует `ta_layers` как источник истины
- [x] **FIXED**: Передача `data.ta_layers` и `data.active_range` в ResearchChart
- [x] **FIXED**: Range overlay рендерится с правильными координатами
- [x] **FIXED**: Приоритет рендеринга: active_range → strict pattern → loose → structure
- [x] **FIXED**: Координаты X clamp к положительным значениям
- [x] Range overlay с голубой заливкой + красной/зелёной границами
- [x] State indicator (ACTIVE) в overlay

### Session 3 - Breakout + Target Projections
- [x] **ADDED**: Break up target projection (зелёная пунктирная линия)
- [x] **ADDED**: Break down target projection (красная пунктирная линия)
- [x] **ADDED**: Target circles с price labels (↑ 82525, ↓ 56518)
- [x] **CLEANED**: Убран мусор (probability badges, mid lines, circles)
- [x] **1 screen = 1 idea**: Range box + R/S lines + 2 scenarios arrows

### Session 4 - TA Explorer / Audit Mode
- [x] **Backend**: Добавлен `ta_explorer` payload в API response
- [x] **Backend**: `_build_ta_explorer()` собирает patterns_all, rejected, dominant
- [x] **Frontend**: TAExplorerPanel с 3 вкладками (Overview, Patterns, 10 Layers)
- [x] **Frontend**: DominantCard показывает winner + why_selected
- [x] **Frontend**: PatternsList показывает все найденные паттерны ranked
- [x] **Frontend**: LayersTable показывает все 10 слоёв expandable

### Session 5 - Pattern Ranking Engine V2 (Context-Aware Decision)
- [x] **Backend**: `pattern_ranking_engine_v2.py` — context-aware scoring
- [x] **Backend**: Structure alignment bonus (+10 / -8)
- [x] **Backend**: HTF alignment bonus (+8 / -6)
- [x] **Backend**: Regime fit bonus (+8 / -4 / +6)
- [x] **Backend**: Conflict penalty when opposing patterns have close scores
- [x] **Backend**: `compute_confidence_state()` — clear / weak / conflicted
- [x] **Backend**: `compute_market_quality()` — high / medium / low + tradeable
- [x] **Frontend**: DominantCard с components breakdown grid
- [x] **Frontend**: CONFLICTED badge + WARNING in why_selected
- [x] **Frontend**: PatternsList с final_score + base_score
- [x] **VERIFIED**: 4H показывает CONFLICTED (H&S 76 vs Double Top 72 — opposing biases)
- [x] **VERIFIED**: market_quality = LOW, tradeable = false

## API Endpoints
- `GET /api/health` - Health check
- `GET /api/ta-engine/mtf/{symbol}?timeframes=1D,4H` - Multi-timeframe analysis

## Response Structure
```json
{
  "tf_map": {
    "1D": {
      "ta_layers": {
        "structure": {"trend": "neutral", "phase": "unknown"},
        "impulse": {"has_impulse": true, "direction": "bullish", "strength": "extreme"},
        "regime": {"regime": "range", "state": "active", "range": {...}},
        "pattern": {"type": "loose_range", "confidence": 0.3},
        "confluence": {"count": 1, "factors": ["impulse_bullish"]},
        "probability": {"bullish": 53, "bearish": 47},
        "scenarios": {"break_up": {...}, "break_down": {...}},
        "timing": {"phase": "mid", "compression": false},
        "narrative": "Market structure is neutral..."
      },
      "active_range": {
        "status": "active",
        "top": 76022.6,
        "bottom": 63019.6,
        "start_time": 1771977600,
        "forward_time": 1776988800
      }
    }
  }
}
```

## Test Results
- Backend: 100% (6/6 tests passed)
- Frontend: 100% (10/10 tests passed)

## Next Action Items
- [ ] Добавить breakout confirmation (свеча закрылась за границей)
- [ ] Добавить retest detection (цена вернулась к границе после breakout)
- [ ] Добавить entry/stop/TP сигналы

## Backlog (P1/P2)
- P1: Breakout confirmation визуализация
- P1: Retest detection и сигналы
- P2: Volume analysis в confluence layer
- P2: Order flow данные
