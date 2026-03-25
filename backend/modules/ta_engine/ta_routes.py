"""
TA Engine Routes
=================
Phase 14.2 — API endpoints for TA Hypothesis Layer.
Includes MTF (Multi-Timeframe) endpoints.

CHART DATA CONFIG:
- Full chart history for scrolling (2000+ candles)
- TA analysis uses subset (150-200 candles)
- Works universally for all assets (BTC, ETH, SOL, SPX, etc.)
"""

from fastapi import APIRouter, Query
from datetime import datetime, timezone
from typing import List, Dict, Any
import time
import os

from modules.ta_engine.hypothesis import get_hypothesis_builder
from modules.ta_engine.per_tf_builder import get_per_timeframe_builder
from modules.ta_engine.mtf import get_mtf_orchestrator
from modules.ta_engine.render_plan import get_render_plan_engine, get_render_plan_engine_v2
from modules.ta_engine.market_state import get_market_state_engine
from modules.ta_engine.patterns.pattern_figure_registry import get_pattern_figure_registry
from modules.ta_engine.structure import StructureVisualizationBuilder
from modules.ta_engine.setup.pattern_validator_v2 import get_pattern_validator_v2
from modules.data.coinbase_auto_init import CoinbaseAutoInit

router = APIRouter(prefix="/api/ta-engine", tags=["ta-engine"])

_builder = get_hypothesis_builder()
_per_tf_builder = get_per_timeframe_builder()
_mtf_orchestrator = get_mtf_orchestrator()
_render_plan_engine = get_render_plan_engine()
_render_plan_engine_v2 = get_render_plan_engine_v2()
_market_state_engine = get_market_state_engine()
_pattern_figure_registry = get_pattern_figure_registry()
_structure_viz_builder = StructureVisualizationBuilder()

# Simple cache for MTF responses (60 seconds TTL)
_mtf_cache: Dict[str, Dict[str, Any]] = {}
_mtf_cache_ttl = 60  # seconds


# ═══════════════════════════════════════════════════════════════
# CHART DATA CONFIG - UNIVERSAL FOR ALL ASSETS
# ═══════════════════════════════════════════════════════════════

# Default chart lookback (full history for scrolling)
# Works for ANY asset from Coinbase
CHART_LOOKBACK = {
    "1m": 1000,
    "5m": 2000,
    "15m": 2000,
    "1h": 2000,
    "4h": 2000,
    "6h": 2000,      # Used for 4H product timeframe
    "1d": 2000,      # ~5.5 years of daily data
    "1w": 500,
}

# TA analysis lookback (for pattern detection)
TA_LOOKBACK = {
    "1m": 100,
    "5m": 100,
    "15m": 150,
    "1h": 168,
    "4h": 200,
    "6h": 200,
    "1d": 150,
    "1w": 52,
}

# Product timeframe to Coinbase granularity mapping
# All 6 supported product timeframes: 4H, 1D, 7D, 1M, 6M, 1Y
TF_CANDLE_MAP = {
    "4H": "6h",      # 6h candles for 4H (Coinbase doesn't have 4h)
    "1D": "1d",      # Daily candles
    "7D": "1d",      # Aggregate daily to weekly
    "1M": "1d",      # Aggregate daily to monthly
    "30D": "1d",     # Alias for 1M
    "6M": "1d",      # Aggregate daily to 6-month
    "180D": "1d",    # Alias for 6M
    "1Y": "1d",      # Aggregate daily to yearly
}

# Aggregation periods (days) for higher timeframes
TF_AGGREGATION = {
    "7D": 7,
    "1M": 30,
    "30D": 30,
    "6M": 180,
    "180D": 180,
    "1Y": 365,
}

# Supported product timeframes (UI)
SUPPORTED_TIMEFRAMES = ["4H", "1D", "7D", "1M", "6M", "1Y"]

def get_chart_lookback(timeframe: str) -> int:
    """Get full chart lookback for scrollable history."""
    tf = timeframe.lower()
    return CHART_LOOKBACK.get(tf, 2000)

def get_ta_lookback(timeframe: str) -> int:
    """Get TA analysis lookback for pattern detection."""
    tf = timeframe.lower()
    return TA_LOOKBACK.get(tf, 150)

def normalize_symbol(symbol: str) -> tuple:
    """
    Normalize symbol to internal and Coinbase formats.
    
    Works for ANY asset - user can request any symbol from Coinbase.
    
    Returns: (internal_symbol, coinbase_product_id)
    
    Examples:
        BTC -> (BTCUSDT, BTC-USD)
        ETH -> (ETHUSDT, ETH-USD)
        AVAX -> (AVAXUSDT, AVAX-USD)
        DOGE -> (DOGEUSDT, DOGE-USD)
    """
    # Clean up symbol
    clean = symbol.upper().replace("USDT", "").replace("USD", "").replace("-", "")
    
    internal = f"{clean}USDT"
    coinbase_id = f"{clean}-USD"
    
    return internal, coinbase_id


def _get_cached_mtf(cache_key: str):
    """Get cached MTF response if still valid."""
    if cache_key in _mtf_cache:
        cached = _mtf_cache[cache_key]
        if time.time() - cached["timestamp"] < _mtf_cache_ttl:
            return cached["data"]
    return None

def _set_cached_mtf(cache_key: str, data: dict):
    """Cache MTF response."""
    _mtf_cache[cache_key] = {
        "data": data,
        "timestamp": time.time()
    }

def get_coinbase_provider():
    """Get Coinbase provider instance."""
    return CoinbaseAutoInit.get_instance()


def _aggregate_candles(candles: List[Dict[str, Any]], period_days: int) -> List[Dict[str, Any]]:
    """
    Aggregate daily candles into higher timeframe candles.
    
    For example:
    - period_days=7 -> weekly candles
    - period_days=30 -> monthly candles
    - period_days=180 -> 6-month candles
    - period_days=365 -> yearly candles
    
    Each aggregated candle:
    - open: first candle's open
    - high: max high in period
    - low: min low in period
    - close: last candle's close
    - volume: sum of volumes
    - time: first candle's timestamp
    """
    if not candles or period_days <= 1:
        return candles
    
    # Sort by time
    sorted_candles = sorted(candles, key=lambda x: x['time'])
    
    aggregated = []
    period_seconds = period_days * 24 * 60 * 60
    
    i = 0
    while i < len(sorted_candles):
        period_start = sorted_candles[i]['time']
        period_end = period_start + period_seconds
        
        # Collect candles in this period
        period_candles = []
        while i < len(sorted_candles) and sorted_candles[i]['time'] < period_end:
            period_candles.append(sorted_candles[i])
            i += 1
        
        if period_candles:
            agg_candle = {
                'time': period_candles[0]['time'],
                'open': period_candles[0]['open'],
                'high': max(c['high'] for c in period_candles),
                'low': min(c['low'] for c in period_candles),
                'close': period_candles[-1]['close'],
                'volume': sum(c.get('volume', 0) for c in period_candles),
            }
            aggregated.append(agg_candle)
    
    return aggregated


# NOTE: Static routes MUST come before dynamic {symbol} routes

@router.get("/status")
async def get_ta_status():
    """Health check for TA Engine."""
    return {
        "ok": True,
        "module": "ta_engine",
        "version": "14.2",
        "phase": "Hypothesis Layer",
        "components": {
            "hypothesis_builder": "active",
            "trend_analyzer": "active",
            "momentum_analyzer": "active",
            "structure_analyzer": "active",
            "breakout_detector": "active",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/chart-config")
async def get_chart_config():
    """
    Get chart data configuration.
    
    Returns lookback settings for all timeframes.
    Works for ANY asset from Coinbase - no restrictions.
    """
    return {
        "ok": True,
        "chart_lookback": CHART_LOOKBACK,
        "ta_lookback": TA_LOOKBACK,
        "tf_candle_map": TF_CANDLE_MAP,
        "tf_aggregation": TF_AGGREGATION,
        "supported_timeframes": SUPPORTED_TIMEFRAMES,
        "description": {
            "chart_lookback": "Full history for chart scrolling",
            "ta_lookback": "Candles used for TA pattern detection",
            "supported_timeframes": "All 6 product timeframes: 4H, 1D, 7D, 1M, 6M, 1Y",
        },
        "note": "Works for ANY asset available on Coinbase exchange",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/hypothesis/batch")
async def get_hypothesis_batch(
    symbols: str = Query("BTC,ETH,SOL", description="Comma-separated symbols"),
    timeframe: str = Query("1d", description="Candle timeframe")
):
    """Get hypothesis for multiple symbols."""
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    results = {}
    for sym in sym_list:
        hypo = _builder.build(sym, timeframe)
        results[sym] = hypo.to_dict()
    return {
        "ok": True,
        "count": len(results),
        "hypotheses": results,
    }


@router.get("/hypothesis/full/{symbol}")
async def get_hypothesis_full(
    symbol: str = "BTC",
    timeframe: str = Query("1d", description="Candle timeframe")
):
    """
    Get full TA hypothesis with detailed component signals.
    """
    hypo = _builder.build(symbol, timeframe)
    return {
        "ok": True,
        "hypothesis": hypo.to_full_dict(),
    }


@router.get("/hypothesis/{symbol}")
async def get_hypothesis(
    symbol: str = "BTC",
    timeframe: str = Query("1d", description="Candle timeframe")
):
    """
    Get unified TA hypothesis for a symbol.
    This is the primary endpoint for Trading Layer.
    
    Returns single direction/conviction after analyzing:
    - Trend (MA alignment)
    - Momentum (RSI, MACD)
    - Structure (HH/HL, BOS)
    - Breakout detection
    """
    hypo = _builder.build(symbol, timeframe)
    return {
        "ok": True,
        "hypothesis": hypo.to_dict(),
    }


# =============================================================================
# MTF (MULTI-TIMEFRAME) ENDPOINTS
# =============================================================================

@router.get("/mtf/{symbol}")
async def get_mtf_analysis(
    symbol: str = "BTC",
    timeframes: str = Query("1D,4H,1H", description="Comma-separated timeframes"),
    bias_tf: str = Query("1D", description="Higher timeframe for bias"),
    setup_tf: str = Query("4H", description="Setup timeframe"),
    entry_tf: str = Query("1H", description="Entry timeframe"),
):
    """
    Get Multi-Timeframe analysis.
    
    Each timeframe is analyzed independently, then orchestrated.
    
    Returns:
    - tf_map: Full TA payload for each timeframe
    - mtf_context: Orchestrated context (alignment, tradeability)
    - default_tf: Recommended timeframe to display
    """
    try:
        # Check cache first
        cache_key = f"{symbol}:{timeframes}"
        cached_data = _get_cached_mtf(cache_key)
        if cached_data:
            print(f"[MTF] Cache hit for {cache_key}")
            return cached_data
        
        print(f"[MTF] Cache miss, building for {cache_key}")
        
        provider = get_coinbase_provider()
        tf_list = [t.strip().upper() for t in timeframes.split(",") if t.strip()]
        
        # Normalize symbol - works for ANY asset from Coinbase
        normalized_symbol, product_id = normalize_symbol(symbol)
        
        # Build per-timeframe data
        tf_map = {}
        
        # TF normalization (1M/6M are proper TA names, 30D/180D are legacy)
        tf_normalize = {
            "1M": "1M", "30D": "1M",   # Monthly
            "6M": "6M", "180D": "6M",  # Semi-annual
        }
        
        # TF to candle type mapping (extends global TF_CANDLE_MAP)
        tf_candle_map = {
            "1H": "1h",
            **TF_CANDLE_MAP,  # 4H, 1D, 7D, 1M, 30D, 6M, 180D, 1Y
        }
        
        # Aggregation periods (extends global TF_AGGREGATION)
        tf_aggregation = {
            **TF_AGGREGATION,  # 7D, 1M, 30D, 6M, 180D, 1Y
        }
        
        for tf in tf_list:
            cb_tf = tf_candle_map.get(tf, "1d")
            ta_lookback = get_ta_lookback(cb_tf)
            full_lookback = get_chart_lookback(cb_tf)
            aggregation_days = tf_aggregation.get(tf)
            
            try:
                # Get FULL candles for chart (scrollable history)
                print(f"[MTF] Getting candles for {tf} ({cb_tf}), limit={full_lookback}...")
                raw_candles = await provider.data_provider.get_candles(
                    product_id=product_id,
                    timeframe=cb_tf,
                    limit=full_lookback
                )
                print(f"[MTF] Got {len(raw_candles)} candles for {tf}")
                
                # Format ALL candles for chart
                all_candles = []
                for c in raw_candles:
                    all_candles.append({
                        "time": c['timestamp'] // 1000 if c['timestamp'] > 1e12 else c['timestamp'],
                        "open": c['open'],
                        "high": c['high'],
                        "low": c['low'],
                        "close": c['close'],
                        "volume": c.get('volume', 0)
                    })
                
                all_candles.sort(key=lambda x: x['time'])
                
                # Aggregate candles for higher timeframes (7D, 30D, 180D, 1Y)
                if aggregation_days and len(all_candles) > 0:
                    all_candles = _aggregate_candles(all_candles, aggregation_days)
                    print(f"[MTF] Aggregated {tf} to {len(all_candles)} candles (period={aggregation_days}d)")
                
                # Use last N candles for TA analysis only
                candles = all_candles[-ta_lookback:] if len(all_candles) > ta_lookback else all_candles
                
                if candles:
                    # Build full TA for this TF
                    print(f"[MTF] Building TA for {tf} with {len(candles)} candles (full: {len(all_candles)})...")
                    tf_data = _per_tf_builder.build(
                        candles=candles,
                        symbol=normalized_symbol,
                        timeframe=tf,
                    )
                    print(f"[MTF] TA built for {tf}")
                    
                    # IMPORTANT: Replace candles in response with FULL history
                    tf_data["candles"] = all_candles
                    tf_data["candles_count"] = len(all_candles)
                    tf_data["ta_lookback"] = len(candles)
                    
                    # Keep candles in response for chart rendering
                    tf_map[tf] = tf_data
                else:
                    tf_map[tf] = _per_tf_builder._empty_result(tf, normalized_symbol)
                    
            except Exception as e:
                print(f"[MTF] Error building TF {tf}: {e}")
                import traceback
                traceback.print_exc()
                tf_map[tf] = _per_tf_builder._empty_result(tf, normalized_symbol)
        
        # Build MTF orchestration
        mtf_context = _mtf_orchestrator.build(
            tf_map=tf_map,
            bias_tf=bias_tf,
            setup_tf=setup_tf,
            entry_tf=entry_tf,
        )
        
        # ═══════════════════════════════════════════════════════════════
        # MTF ALIGNMENT ENGINE — связываем TF между собой (NEW!)
        # ═══════════════════════════════════════════════════════════════
        try:
            from modules.ta_engine.mtf_alignment_engine import build_mtf_alignment, get_alignment_summary
            from modules.ta_engine.narrative_engine import build_mtf_narrative
            
            # Build alignment from tf_map
            alignment = build_mtf_alignment(tf_map)
            alignment_summary = get_alignment_summary(alignment)
            
            # Build MTF narrative
            mtf_narrative = build_mtf_narrative(tf_map, alignment)
            
            # Add to mtf_context
            if isinstance(mtf_context, dict):
                mtf_context["alignment"] = alignment
                mtf_context["alignment_summary"] = alignment_summary
                mtf_context["mtf_narrative"] = mtf_narrative
                
            print(f"[MTF] Alignment: {alignment.get('direction')} ({alignment.get('confidence')})")
            print(f"[MTF] MTF Narrative: {mtf_narrative.get('short', '')[:60]}")
        except Exception as e:
            print(f"[MTF] Alignment/Narrative error: {e}")
        
        # Add interpretation summary_text for frontend
        try:
            from modules.ta_engine.interpretation.interpretation_engine import get_interpretation_engine
            ie = get_interpretation_engine()
            
            # Get data from each TF role
            htf_data = None
            mtf_data = None
            ltf_data = None
            
            for tf in ["1Y", "6M", "180D", "30D", "1M"]:
                if tf in tf_map and tf_map[tf].get("candles"):
                    htf_data = tf_map[tf]
                    break
            for tf in ["7D", "1D"]:
                if tf in tf_map and tf_map[tf].get("candles"):
                    mtf_data = tf_map[tf]
                    break
            if "4H" in tf_map and tf_map["4H"].get("candles"):
                ltf_data = tf_map["4H"]
            
            # Build one-line summary
            summary_text = ie.build_one_line_summary(htf_data, mtf_data, ltf_data)
            
            # Ensure mtf_context has summary dict with summary_text
            if isinstance(mtf_context, dict):
                mtf_context["summary"] = {
                    "text": mtf_context.get("summary", ""),
                    "summary_text": summary_text,
                }
            print(f"[MTF] Summary text: {summary_text}")
        except Exception as e:
            print(f"[MTF] Failed to build summary_text: {e}")
        
        result = {
            "ok": True,
            "symbol": normalized_symbol,
            "tf_map": tf_map,
            "mtf_context": mtf_context,
            "default_tf": setup_tf,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        # Cache result
        _set_cached_mtf(cache_key, result)
        print(f"[MTF] Cached result for {cache_key}")
        
        return result
    
    except Exception as e:
        import traceback
        print(f"[MTF] Error: {e}")
        traceback.print_exc()
        return {
            "ok": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@router.get("/mtf/{symbol}/{timeframe}")
async def get_single_tf_analysis(
    symbol: str = "BTC",
    timeframe: str = "4H",
):
    """
    Get analysis for a single timeframe.
    
    Returns full TA payload including candles.
    """
    try:
        provider = get_coinbase_provider()
        
        # Normalize symbol
        clean_symbol = symbol.upper().replace("USDT", "").replace("USD", "")
        normalized_symbol = f"{clean_symbol}USDT"
        product_id = f"{clean_symbol}-USD"
        
        # TF to candle type mapping
        # Note: Coinbase doesn't support 4h, using 6h instead
        tf_candle_map = {
            "1H": "1h",
            "4H": "6h", 
            "1D": "1d",
            "7D": "1d",
            "30D": "1d",
        }
        
        # Lookback config
        tf_lookback = {
            "1H": 168,
            "4H": 200,
            "1D": 150,
            "7D": 400,
            "30D": 800,
        }
        
        cb_tf = tf_candle_map.get(timeframe.upper(), "1d")
        lookback = tf_lookback.get(timeframe.upper(), 150)
        
        raw_candles = await provider.data_provider.get_candles(
            product_id=product_id,
            timeframe=cb_tf,
            limit=lookback + 50
        )
        
        if not raw_candles:
            return {
                "ok": False,
                "error": "No candles available",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        
        # Format candles
        candles = []
        for c in raw_candles:
            candles.append({
                "time": c['timestamp'] // 1000 if c['timestamp'] > 1e12 else c['timestamp'],
                "open": c['open'],
                "high": c['high'],
                "low": c['low'],
                "close": c['close'],
                "volume": c.get('volume', 0)
            })
        
        candles.sort(key=lambda x: x['time'])
        candles = candles[-lookback:]
        
        # Build full TA
        tf_data = _per_tf_builder.build(
            candles=candles,
            symbol=normalized_symbol,
            timeframe=timeframe.upper(),
        )
        
        return {
            "ok": True,
            "symbol": normalized_symbol,
            "timeframe": timeframe.upper(),
            "data": tf_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    except Exception as e:
        import traceback
        print(f"[MTF Single TF] Error: {e}")
        traceback.print_exc()
        return {
            "ok": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }



# =============================================================================
# RENDER PLAN ENDPOINT
# =============================================================================

@router.get("/render-plan/{symbol}")
async def get_render_plan(
    symbol: str = "BTC",
    timeframe: str = Query("1D", description="Timeframe for analysis"),
):
    """
    Get RENDER PLAN for visualization.
    
    This is the BRAIN of visualization:
    - Filters data to show only what matters
    - Prioritizes based on regime (trend/range/reversal)
    - Returns focused visualization: 1 graph = 1 setup = 1 story
    
    Returns:
    - execution: entry/stop/targets
    - pattern: active pattern (if relevant)
    - poi: closest zone only (not 5)
    - structure: simplified swings/choch/bos
    - liquidity: limited eq/sweeps
    - displacement: latest only
    - indicators: regime-appropriate
    - meta: regime + focus
    - chain_highlight: sweep -> choch -> entry storytelling
    """
    try:
        provider = get_coinbase_provider()
        
        # Normalize symbol
        clean_symbol = symbol.upper().replace("USDT", "").replace("USD", "")
        normalized_symbol = f"{clean_symbol}USDT"
        product_id = f"{clean_symbol}-USD"
        
        # TF mapping
        tf_candle_map = {
            "1H": "1h",
            "4H": "6h",
            "1D": "1d",
        }
        tf_lookback = {
            "1H": 168,
            "4H": 200,
            "1D": 150,
        }
        
        cb_tf = tf_candle_map.get(timeframe.upper(), "1d")
        lookback = tf_lookback.get(timeframe.upper(), 150)
        
        # Get candles
        raw_candles = await provider.data_provider.get_candles(
            product_id=product_id,
            timeframe=cb_tf,
            limit=lookback + 50
        )
        
        if not raw_candles:
            return {
                "ok": False,
                "error": "No candles available",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        
        # Format candles
        candles = []
        for c in raw_candles:
            candles.append({
                "time": c['timestamp'] // 1000 if c['timestamp'] > 1e12 else c['timestamp'],
                "open": c['open'],
                "high": c['high'],
                "low": c['low'],
                "close": c['close'],
                "volume": c.get('volume', 0)
            })
        
        candles.sort(key=lambda x: x['time'])
        candles = candles[-lookback:]
        
        current_price = candles[-1]['close'] if candles else 0
        
        # Build full TA first
        tf_data = _per_tf_builder.build(
            candles=candles,
            symbol=normalized_symbol,
            timeframe=timeframe.upper(),
        )
        
        # Extract components for render_plan
        execution = tf_data.get("execution", {})
        primary_pattern = tf_data.get("primary_pattern")
        structure_context = tf_data.get("structure_context", {})
        liquidity = tf_data.get("liquidity", {})
        displacement = tf_data.get("displacement", {})
        poi = tf_data.get("poi", {})
        indicators = tf_data.get("indicators", {})
        
        # Build render_plan
        render_plan = _render_plan_engine.build(
            execution=execution,
            primary_pattern=primary_pattern,
            structure_context=structure_context,
            liquidity=liquidity,
            displacement=displacement,
            poi=poi,
            indicators=indicators,
            current_price=current_price,
        )
        
        return {
            "ok": True,
            "symbol": normalized_symbol,
            "timeframe": timeframe.upper(),
            "current_price": current_price,
            "render_plan": render_plan,
            "candles": candles,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    except Exception as e:
        import traceback
        print(f"[Render Plan] Error: {e}")
        traceback.print_exc()
        return {
            "ok": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }



# =============================================================================
# PATTERN REGISTRY ENDPOINT
# =============================================================================

@router.get("/registry/patterns")
async def get_pattern_registry():
    """
    Get full pattern figure registry.
    
    Returns 50+ registered pattern figures organized by category:
    - reversal (13+)
    - continuation (14+)
    - harmonic (12+)
    - candlestick (15+)
    - complex (8+)
    """
    return {
        "ok": True,
        "registry": _pattern_figure_registry.to_dict(),
        "total": _pattern_figure_registry.count(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# RENDER PLAN V2 ENDPOINT (6 LAYERS)
# =============================================================================

@router.get("/render-plan-v2/{symbol}")
async def get_render_plan_v2(
    symbol: str = "BTC",
    timeframe: str = Query("1D", description="Timeframe: 4H, 1D, 7D, 30D, 180D, 1Y"),
):
    """
    Get RENDER PLAN V2 with 6 isolated layers.
    
    Product Timeframes: 4H, 1D, 7D, 30D, 180D, 1Y
    
    Layers:
    A. Market State (trend, channel, volatility, momentum, wyckoff)
    B. Structure (swings, HH/HL/LH/LL, BOS, CHOCH)
    C. Indicators (overlays, panes)
    D. Pattern Figures (ONLY from registry - NOT channel/trend)
    E. Liquidity (EQH/EQL, sweeps, OB, FVG)
    F. Execution (ALWAYS visible: valid/waiting/no_trade)
    
    Key rules:
    - 1 timeframe = 1 isolated world
    - Each TF renders its own complete TA analysis
    """
    try:
        provider = get_coinbase_provider()
        
        # Normalize symbol - works for ANY asset from Coinbase
        normalized_symbol, product_id = normalize_symbol(symbol)
        
        # All 6 supported product timeframes: 4H, 1D, 7D, 1M, 6M, 1Y
        # Also accept legacy aliases: 30D -> 1M, 180D -> 6M
        tf_upper = timeframe.upper()
        tf_normalize = {"30D": "1M", "180D": "6M"}
        tf_upper = tf_normalize.get(tf_upper, tf_upper)
        
        if tf_upper not in SUPPORTED_TIMEFRAMES:
            tf_upper = "1D"
        
        # Coinbase timeframe mapping (use global TF_CANDLE_MAP)
        cb_tf = TF_CANDLE_MAP.get(tf_upper, "1d")
        
        # Get lookbacks from global config functions
        ta_lookback_count = get_ta_lookback(cb_tf)
        full_lookback = get_chart_lookback(cb_tf)
        
        # Check if aggregation needed
        aggregation_days = TF_AGGREGATION.get(tf_upper)
        
        # Get FULL candles for chart (scrollable history)
        raw_candles = await provider.data_provider.get_candles(
            product_id=product_id,
            timeframe=cb_tf,
            limit=full_lookback
        )
        
        if not raw_candles:
            return {
                "ok": False,
                "error": f"No candles available for {symbol}. Check if this asset exists on Coinbase.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        
        # Format ALL candles for CHART (full scrollable history)
        all_candles = []
        for c in raw_candles:
            all_candles.append({
                "time": c['timestamp'] // 1000 if c['timestamp'] > 1e12 else c['timestamp'],
                "open": c['open'],
                "high": c['high'],
                "low": c['low'],
                "close": c['close'],
                "volume": c.get('volume', 0)
            })
        
        all_candles.sort(key=lambda x: x['time'])
        
        # Aggregate candles for higher timeframes (7D, 1M, 6M, 1Y)
        if aggregation_days and len(all_candles) > 0:
            all_candles = _aggregate_candles(all_candles, aggregation_days)
            print(f"[RenderV2] Aggregated {tf_upper} to {len(all_candles)} candles (period={aggregation_days}d)")
        
        # Use last N candles for TA analysis only (not for chart)
        candles = all_candles[-ta_lookback_count:] if len(all_candles) > ta_lookback_count else all_candles
        
        current_price = all_candles[-1]['close'] if all_candles else 0
        
        # Build full TA
        tf_data = _per_tf_builder.build(
            candles=candles,
            symbol=normalized_symbol,
            timeframe=tf_upper,
        )
        
        # Compute market state (Layer A)
        market_state = _market_state_engine.analyze(candles)
        
        # Build structure visualization (swings, BOS, CHOCH for chart)
        # First get pivots
        tf_config = {
            "4H": {"lookback": 200, "pivot_window": 5, "min_pivot_distance": 10, "pattern_window": 150, "candle_type": "4h"},
            "1D": {"lookback": 300, "pivot_window": 7, "min_pivot_distance": 15, "pattern_window": 200, "candle_type": "1d"},
        }.get(tf_upper, {"lookback": 300, "pivot_window": 7, "min_pivot_distance": 15, "pattern_window": 200, "candle_type": "1d"})
        
        validator = get_pattern_validator_v2(tf_upper, tf_config)
        pivot_highs_raw, pivot_lows_raw = validator.find_pivots(candles)
        
        # Build structure visualization with swings, events, trendlines
        structure_context = tf_data.get("structure_context", {})
        structure_viz = _structure_viz_builder.build(
            pivots_high=pivot_highs_raw,
            pivots_low=pivot_lows_raw,
            structure_context=structure_context,
            candles=candles,
        )
        
        # Merge structure context metrics with visualization data
        # Extract BOS/CHOCH from events list
        events = structure_viz.get("events", [])
        bos_event = next((e for e in events if "bos" in e.get("type", "")), None)
        choch_event = next((e for e in events if "choch" in e.get("type", "")), None)
        
        structure = {
            **structure_context,
            "swings": structure_viz.get("pivot_points", []),
            "bos": bos_event,
            "choch": choch_event,
            "active_trendlines": structure_viz.get("active_trendlines", []),
        }
        
        indicators = tf_data.get("indicators", {})
        liquidity = tf_data.get("liquidity", {})
        execution = tf_data.get("execution", {})
        poi = tf_data.get("poi", {})
        
        # Get patterns (convert primary_pattern to list)
        # IMPORTANT: Also include pattern_render_contract for range patterns
        patterns = []
        primary = tf_data.get("primary_pattern")
        if primary:
            patterns.append(primary)
        
        # V2: Include pattern_render_contract (range, loose_range, etc.)
        prc = tf_data.get("pattern_render_contract")
        if prc and prc.get("display_approved"):
            # Convert pattern_render_contract to pattern format
            prc_type = prc.get("type", "")
            # Check if this is a range-type pattern
            if "range" in prc_type.lower():
                # Transform to range pattern format for render_plan
                range_pattern = {
                    "type": prc_type,
                    "is_active": True,  # Range is active until breakout
                    "confidence": prc.get("confidence", 0.5),
                    "direction": prc.get("bias", "neutral"),
                    "state": prc.get("state", "active"),
                    "forward_bars": 30,  # 30 bars forward extension
                    "points": {},
                    "breakout_level": prc.get("meta", {}).get("resistance"),
                    "invalidation": prc.get("meta", {}).get("support"),
                }
                
                # Extract boundaries from meta
                boundaries = prc.get("meta", {}).get("boundaries", {})
                if boundaries:
                    upper = boundaries.get("upper", {})
                    lower = boundaries.get("lower", {})
                    
                    # Calculate forward extension time
                    if candles and len(candles) >= 2:
                        interval = candles[-1].get("time", 0) - candles[-2].get("time", 0)
                        if interval > 1e12:
                            interval = interval // 1000
                        forward_time = candles[-1].get("time", 0)
                        if forward_time > 1e12:
                            forward_time = forward_time // 1000
                        forward_time = forward_time + interval * 30  # 30 bars forward
                    else:
                        forward_time = upper.get("x2", 0) + 86400 * 30  # 30 days
                    
                    # CRITICAL: Range lines must be PARALLEL and extend forward
                    resistance = prc.get("meta", {}).get("resistance", upper.get("y2", 0))
                    support = prc.get("meta", {}).get("support", lower.get("y2", 0))
                    
                    range_pattern["points"] = {
                        "upper": [
                            {"time": upper.get("x1", 0), "value": resistance},
                            {"time": forward_time, "value": resistance},  # PARALLEL - same price
                        ],
                        "lower": [
                            {"time": lower.get("x1", 0), "value": support},
                            {"time": forward_time, "value": support},  # PARALLEL - same price
                        ],
                        "mid": [
                            {"time": upper.get("x1", 0), "value": (resistance + support) / 2},
                            {"time": forward_time, "value": (resistance + support) / 2},
                        ],
                    }
                
                patterns.append(range_pattern)
                print(f"[RenderPlanV2] Added range pattern: {prc_type}, forward_time={forward_time}")
        
        
        # Build render plan v2
        render_plan = _render_plan_engine_v2.build(
            timeframe=tf_upper,
            current_price=current_price,
            market_state=market_state.to_dict(),
            structure=structure,
            indicators=indicators,
            patterns=patterns,
            liquidity=liquidity,
            execution=execution,
            poi=poi,
        )
        
        return {
            "ok": True,
            "symbol": normalized_symbol,
            "timeframe": tf_upper,
            "current_price": current_price,
            "render_plan": render_plan,
            "candles": all_candles,  # Full history for chart scrolling
            "candles_count": len(all_candles),
            "ta_lookback": len(candles),  # How many candles used for TA
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    except Exception as e:
        import traceback
        print(f"[Render Plan V2] Error: {e}")
        traceback.print_exc()
        return {
            "ok": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# =============================================================================
# INDICATOR REGISTRY ENDPOINT
# =============================================================================

@router.get("/registry/indicators")
async def get_indicator_registry():
    """
    Get full indicator registry.
    
    Returns 30+ indicators organized by type:
    - overlays (on main chart)
    - oscillators (separate pane, bounded)
    - momentum (separate pane, unbounded)
    - volume
    - volatility
    - trend
    """
    from modules.ta_engine.indicators import get_indicator_registry
    registry = get_indicator_registry()
    
    return {
        "ok": True,
        "registry": registry.to_dict(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
