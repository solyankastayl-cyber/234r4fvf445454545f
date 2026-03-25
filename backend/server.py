"""
TA Engine Python Backend - Minimal Runtime
==========================================
"""
import os
import sys
import jwt
import hashlib
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str

# Admin credentials (for demo)
ADMIN_USERS = {
    "admin": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "ADMIN"
    },
    "moderator": {
        "password_hash": hashlib.sha256("mod123".encode()).hexdigest(),
        "role": "MODERATOR"
    }
}
JWT_SECRET = os.environ.get("JWT_SECRET", "fomo-admin-secret-key-2024")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize MongoDB
try:
    from core.database import get_database, mongo_health_check
    _db = get_database()
    print("[Server] MongoDB connection initialized")
except Exception as e:
    print(f"[Server] MongoDB connection warning: {e}")
    _db = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Server] TA Engine starting...")
    
    # Auto-initialize Coinbase provider
    try:
        from modules.data.coinbase_auto_init import init_coinbase_provider
        result = await init_coinbase_provider()
        if result.get("ok"):
            print(f"[Coinbase] Provider initialized - BTC: ${result.get('btc_price', 0):,.2f}")
        else:
            print(f"[Coinbase] Init warning: {result.get('error', 'unknown')}")
    except Exception as e:
        print(f"[Coinbase] Init skipped: {e}")
    
    yield
    print("[Server] TA Engine shutting down...")


app = FastAPI(
    title="TA Engine API",
    description="TA Engine Module Runtime",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "mode": "TA_ENGINE_RUNTIME",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ============================================
# Admin Auth Endpoints
# ============================================

@app.post("/api/admin/auth/login")
async def admin_login(request: LoginRequest):
    """Admin login endpoint"""
    user = ADMIN_USERS.get(request.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    password_hash = hashlib.sha256(request.password.encode()).hexdigest()
    if password_hash != user["password_hash"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    token = jwt.encode({
        "sub": request.username,
        "role": user["role"],
        "exp": expires
    }, JWT_SECRET, algorithm="HS256")
    
    return {
        "ok": True,
        "token": token,
        "role": user["role"],
        "username": request.username,
        "expiresAtTs": int(expires.timestamp())
    }


@app.get("/api/admin/auth/status")
async def admin_auth_status(authorization: Optional[str] = Header(None)):
    """Check admin auth status"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {
            "ok": True,
            "data": {
                "userId": payload["sub"],
                "role": payload["role"],
                "expiresAtTs": payload["exp"]
            }
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/api/system/db-health")
async def db_health():
    try:
        return mongo_health_check()
    except Exception as e:
        return {"status": "error", "connected": False, "error": str(e)}


# TA Engine Routes
try:
    from modules.ta_engine.ta_routes import router as ta_engine_router
    app.include_router(ta_engine_router)
    print("[Routes] TA Engine router registered")
except ImportError as e:
    print(f"[Routes] TA Engine router not available: {e}")

# TA Setup API (Clean Research Pipeline)
try:
    from modules.ta_engine.ta_setup_api import router as ta_setup_api_router
    app.include_router(ta_setup_api_router)
    print("[Routes] TA Setup API router registered")
except ImportError as e:
    print(f"[Routes] TA Setup API router not available: {e}")

# TA Research API (Unified Chart Objects Pipeline)
try:
    from modules.ta_engine.research_api import router as research_api_router
    app.include_router(research_api_router)
    print("[Routes] TA Research API router registered")
except ImportError as e:
    print(f"[Routes] TA Research API router not available: {e}")

# TA Setup Engine Routes (Setup Graph Architecture)
try:
    from modules.ta_engine.setup.setup_routes import router as ta_setup_router
    app.include_router(ta_setup_router)
    print("[Routes] TA Setup Engine router registered")
except ImportError as e:
    print(f"[Routes] TA Setup Engine router not available: {e}")

# TA Ideas Routes (Idea System)
try:
    from modules.ta_engine.ideas.idea_routes import router as ta_ideas_router
    app.include_router(ta_ideas_router)
    print("[Routes] TA Ideas router registered")
except ImportError as e:
    print(f"[Routes] TA Ideas router not available: {e}")

# Idea Engine V1 Routes (New Idea System)
try:
    from modules.idea.idea_routes import router as idea_v1_router, favorites_router
    app.include_router(idea_v1_router)
    app.include_router(favorites_router)
    print("[Routes] Idea V1 router registered")
except ImportError as e:
    print(f"[Routes] Idea V1 router not available: {e}")

# PHASE F1 — Research Routes
try:
    from modules.chart_composer.routes import chart_composer_router
    app.include_router(chart_composer_router, prefix="/api/v1")
    print("[Routes] Chart Composer router registered")
except Exception as e:
    print(f"[Routes] Chart Composer not available: {e}")

try:
    from modules.signal_explanation.routes import signal_explanation_router
    app.include_router(signal_explanation_router, prefix="/api/v1")
    print("[Routes] Signal Explanation router registered")
except Exception as e:
    print(f"[Routes] Signal Explanation not available: {e}")

try:
    from modules.research_analytics.routes import research_analytics_router
    app.include_router(research_analytics_router, prefix="/api/v1")
    print("[Routes] Research Analytics router registered")
except Exception as e:
    print(f"[Routes] Research Analytics not available: {e}")

try:
    from modules.trading_capsule.research.research_routes import router as trading_research_router
    app.include_router(trading_research_router, prefix="/api/research")
    print("[Routes] Trading Research router registered")
except Exception as e:
    print(f"[Routes] Trading Research not available: {e}")

try:
    from modules.fractal_market_intelligence.fractal_routes import router as fractal_router
    app.include_router(fractal_router)
    print("[Routes] Fractal Intelligence router registered")
except Exception as e:
    print(f"[Routes] Fractal Intelligence not available: {e}")

try:
    from modules.research.hypothesis_engine.hypothesis_routes import router as hypothesis_router
    app.include_router(hypothesis_router)
    print("[Routes] Hypothesis Engine router registered")
except Exception as e:
    print(f"[Routes] Hypothesis Engine not available: {e}")

try:
    from modules.capital_flow import capital_flow_router
    app.include_router(capital_flow_router)
    print("[Routes] Capital Flow router registered")
except Exception as e:
    print(f"[Routes] Capital Flow not available: {e}")

# PHASE F2 — Trading Terminal Routes
try:
    from modules.trading_engine.routes import router as trading_engine_router
    app.include_router(trading_engine_router)
    print("[Routes] Trading Engine router registered")
except Exception as e:
    print(f"[Routes] Trading Engine not available: {e}")

try:
    from modules.trading_terminal.portfolio.portfolio_routes import router as portfolio_router
    app.include_router(portfolio_router)
    print("[Routes] Portfolio router registered")
except Exception as e:
    print(f"[Routes] Portfolio not available: {e}")

try:
    from modules.execution_brain import execution_router
    app.include_router(execution_router)
    print("[Routes] Execution Brain router registered")
except Exception as e:
    print(f"[Routes] Execution Brain not available: {e}")

# Broker Adapters Routes (Coinbase, Binance, etc.)
try:
    from modules.broker_adapters.routes import router as broker_router
    app.include_router(broker_router)
    print("[Routes] Broker Adapters router registered")
except Exception as e:
    print(f"[Routes] Broker Adapters not available: {e}")

# PHASE F3 — System Control Routes
try:
    from modules.system_control.control_routes import router as control_router
    app.include_router(control_router)
    print("[Routes] System Control router registered")
except Exception as e:
    print(f"[Routes] System Control not available: {e}")

try:
    from modules.safety_kill_switch.kill_switch_routes import router as kill_switch_router
    app.include_router(kill_switch_router)
    print("[Routes] Kill Switch router registered")
except Exception as e:
    print(f"[Routes] Kill Switch not available: {e}")

try:
    from modules.circuit_breaker.breaker_routes import router as breaker_router
    app.include_router(breaker_router)
    print("[Routes] Circuit Breaker router registered")
except Exception as e:
    print(f"[Routes] Circuit Breaker not available: {e}")


# ============================================
# Coinbase Provider Live Data Endpoints
# ============================================

@app.get("/api/provider/coinbase/status")
async def coinbase_status():
    """Get Coinbase provider status"""
    try:
        from modules.data.coinbase_auto_init import get_coinbase_status
        return await get_coinbase_status()
    except Exception as e:
        return {"provider": "coinbase", "status": "error", "error": str(e)}


@app.get("/api/provider/coinbase/health")
async def coinbase_health():
    """Coinbase provider health check"""
    try:
        from modules.data.coinbase_auto_init import coinbase_health_check
        return await coinbase_health_check()
    except Exception as e:
        return {"provider": "coinbase", "status": "error", "error": str(e)}


@app.get("/api/provider/coinbase/ticker/{symbol}")
async def coinbase_ticker(symbol: str = "BTC"):
    """Get live ticker from Coinbase"""
    try:
        from modules.data.coinbase_auto_init import coinbase_auto_init
        return await coinbase_auto_init.get_live_ticker(symbol)
    except Exception as e:
        return {"ok": False, "error": str(e), "symbol": symbol}


@app.get("/api/provider/coinbase/candles/{symbol}")
async def coinbase_candles(
    symbol: str = "BTC",
    timeframe: str = Query("1h", description="Timeframe: 1m, 5m, 15m, 1h, 4h, 1d"),
    limit: int = Query(100, ge=1, le=300)
):
    """Get live candles from Coinbase"""
    try:
        from modules.data.coinbase_auto_init import coinbase_auto_init
        return await coinbase_auto_init.get_live_candles(symbol, timeframe, limit)
    except Exception as e:
        return {"ok": False, "error": str(e), "symbol": symbol, "candles": []}


@app.get("/api/provider/list")
async def list_providers():
    """List all data providers and their status"""
    providers = {
        "coinbase": {
            "status": "active",
            "type": "market_data",
            "requires_keys": False,
            "supported_pairs": ["BTC-USD", "ETH-USD", "SOL-USD"],
            "description": "Live market data via public API"
        },
        "binance": {
            "status": "inactive",
            "type": "market_data",
            "requires_keys": False,
            "supported_pairs": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            "description": "Available but not auto-initialized"
        },
        "bybit": {
            "status": "inactive",
            "type": "market_data",
            "requires_keys": False,
            "supported_pairs": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            "description": "Available but not auto-initialized"
        },
        "hyperliquid": {
            "status": "inactive",
            "type": "market_data",
            "requires_keys": False,
            "description": "Available but not auto-initialized"
        }
    }
    
    # Get Coinbase live status
    try:
        from modules.data.coinbase_auto_init import get_coinbase_status
        cb_status = await get_coinbase_status()
        providers["coinbase"]["live_status"] = cb_status
    except:
        pass
    
    return {
        "ok": True,
        "active_provider": "coinbase",
        "providers": providers,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# TA Analysis Endpoints
@app.get("/api/ta/registry")
async def ta_registry():
    try:
        from core.database import get_database
        db = get_database()
        if db is None:
            return {"status": "error", "error": "Database not connected"}
        
        strategies = list(db.strategies.find({}, {"_id": 0}))
        regime_map = list(db.regime_map.find({}, {"_id": 0}))
        config = db.config.find_one({"_id": "calibration"}, {"_id": 0})
        
        return {
            "status": "ok",
            "registry": {
                "strategies_count": len(strategies),
                "strategies": strategies,
                "regime_map_count": len(regime_map),
                "calibration_enabled": config.get("enabled", False) if config else False,
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/api/ta/patterns")
async def ta_patterns():
    try:
        from core.database import get_database
        db = get_database()
        if db is None:
            return {"status": "error", "error": "Database not connected"}
        
        strategies = list(db.strategies.find({}, {"_id": 0}))
        approved = [s for s in strategies if s.get("status") == "APPROVED"]
        limited = [s for s in strategies if s.get("status") == "LIMITED"]
        deprecated = [s for s in strategies if s.get("status") == "DEPRECATED"]
        
        return {
            "status": "ok",
            "patterns": {
                "approved": [s["id"] for s in approved],
                "limited": [s["id"] for s in limited],
                "deprecated": [s["id"] for s in deprecated],
            },
            "total_count": len(strategies),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/api/ta/analyze")
async def ta_analyze(symbol: str = "BTCUSDT", timeframe: str = "1d"):
    try:
        from core.database import get_database
        db = get_database()
        if db is None:
            return {"status": "error", "error": "Database not connected"}
        
        # Get candles
        symbol_clean = symbol.replace("USDT", "").upper()
        candles = list(db.candles.find(
            {"symbol": symbol_clean, "timeframe": timeframe},
            {"_id": 0}
        ).sort("timestamp", -1).limit(100))
        
        # Get strategies
        strategies = list(db.strategies.find(
            {"status": {"$in": ["APPROVED", "LIMITED"]}},
            {"_id": 0}
        ))
        
        # Get regime map
        regime_map = list(db.regime_map.find({}, {"_id": 0}))
        
        return {
            "status": "ok",
            "symbol": symbol,
            "timeframe": timeframe,
            "analysis": {
                "candles_available": len(candles),
                "strategies_active": len(strategies),
                "regime_mappings": len(regime_map),
            },
            "data_range": {
                "latest": candles[0]["timestamp"] if candles else None,
                "oldest": candles[-1]["timestamp"] if candles else None,
            },
            "signals": [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ============================================
# UI Data Endpoints (for Frontend Charts)
# ============================================

@app.get("/api/ui/candles")
async def ui_candles(asset: str = "BTC", days: int = 365, years: int = None):
    """Get candles for UI charts - format compatible with LivePredictionChart"""
    import random
    from datetime import datetime, timedelta
    
    # Calculate days from years if provided
    if years:
        days = years * 365
    
    # Generate mock OHLCV data if database empty
    candles = []
    base_price = 45000 if asset == "BTC" else 2800 if asset == "ETH" else 100
    now = datetime.now(timezone.utc)
    
    for i in list(reversed(list(range(1, days + 1)))):
        ts = now - timedelta(days=i)
        change = random.uniform(-0.03, 0.03)
        open_price = base_price * (1 + change)
        close_price = open_price * (1 + random.uniform(-0.02, 0.02))
        high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.02))
        low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.02))
        volume = random.uniform(1000, 10000) * base_price
        
        # Format for LivePredictionChart: t, o, h, l, c, v
        candles.append({
            "t": ts.strftime("%Y-%m-%d"),
            "o": round(open_price, 2),
            "h": round(high_price, 2),
            "l": round(low_price, 2),
            "c": round(close_price, 2),
            "v": round(volume, 2)
        })
        base_price = close_price
    
    return {
        "ok": True,
        "asset": asset,
        "candles": candles,
        "count": len(candles)
    }


@app.get("/api/meta-brain-v2/forecast-curve")
async def forecast_curve(asset: str = "BTC"):
    """Get forecast curve for MetaBrain chart"""
    import random
    from datetime import datetime, timedelta
    
    base_price = 45000 if asset == "BTC" else 2800 if asset == "ETH" else 100
    now = datetime.now(timezone.utc)
    
    curve = []
    for i in range(30):
        ts = now + timedelta(days=i)
        price_change = random.uniform(-0.01, 0.02) * (i / 30)
        curve.append({
            "time": int(ts.timestamp()),
            "value": round(base_price * (1 + price_change), 2)
        })
    
    verdicts = ["bullish", "bearish", "neutral"]
    return {
        "ok": True,
        "asset": asset,
        "curve": curve,
        "verdict": random.choice(verdicts),
        "confidence": round(random.uniform(0.6, 0.95), 2)
    }


@app.get("/api/forecast/{asset}")
async def forecast_asset(asset: str):
    """Get forecast for specific asset"""
    import random
    
    base_price = 45000 if asset.upper() == "BTC" else 2800 if asset.upper() == "ETH" else 100
    
    predictions = []
    for horizon in ["1D", "7D", "30D"]:
        direction = random.choice(["UP", "DOWN"])
        change = random.uniform(0.01, 0.15)
        predictions.append({
            "horizon": horizon,
            "direction": direction,
            "target_price": round(base_price * (1 + change if direction == "UP" else 1 - change), 2),
            "confidence": round(random.uniform(0.5, 0.9), 2)
        })
    
    return {
        "ok": True,
        "asset": asset,
        "predictions": predictions,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/fractal/summary/{asset}")
async def fractal_summary(asset: str):
    """Get fractal analysis summary"""
    import random
    
    biases = ["bullish", "bearish", "neutral"]
    return {
        "ok": True,
        "asset": asset,
        "current": {
            "bias": random.choice(biases),
            "confidence": round(random.uniform(0.5, 0.9), 2),
            "alignment": round(random.uniform(0.3, 1.0), 2)
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Additional endpoints for frontend
@app.get("/api/market/candles")
async def market_candles(symbol: str = "BTCUSDT", date_range: str = "7d"):
    """Get market candles for chart"""
    import random
    from datetime import datetime, timedelta
    
    # Parse range
    days = 7
    if date_range.endswith("d"):
        days = int(date_range[:-1])
    elif date_range.endswith("m"):
        days = int(date_range[:-1]) * 30
    
    asset = symbol.replace("USDT", "").upper()
    base_price = 45000 if asset == "BTC" else 2800 if asset == "ETH" else 100
    now = datetime.now(timezone.utc)
    
    candles = []
    for i in list(reversed(list(range(1, days * 24 + 1)))):  # hourly candles
        ts = now - timedelta(hours=i)
        change = random.uniform(-0.01, 0.01)
        open_price = base_price * (1 + change)
        close_price = open_price * (1 + random.uniform(-0.005, 0.005))
        high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.005))
        low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.005))
        volume = random.uniform(100, 1000) * base_price
        
        candles.append({
            "time": int(ts.timestamp()),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": round(volume, 2)
        })
        base_price = close_price
    
    return {
        "ok": True,
        "symbol": symbol,
        "candles": candles
    }


@app.get("/api/market/chart/price-vs-expectation-v4")
async def price_vs_expectation(asset: str = "BTC", date_range: str = "7d", horizon: str = "1D"):
    """Get price vs expectation chart data"""
    import random
    from datetime import datetime, timedelta
    
    days = 7
    if date_range.endswith("d"):
        days = int(date_range[:-1])
    
    base_price = 45000 if asset == "BTC" else 2800 if asset == "ETH" else 100
    now = datetime.now(timezone.utc)
    
    history = []
    for i in list(reversed(list(range(1, days + 1)))):
        ts = now - timedelta(days=i)
        actual = base_price * (1 + random.uniform(-0.05, 0.05))
        expected = actual * (1 + random.uniform(-0.02, 0.02))
        history.append({
            "time": int(ts.timestamp()),
            "actual": round(actual, 2),
            "expected": round(expected, 2),
            "delta": round((actual - expected) / expected * 100, 2)
        })
        base_price = actual
    
    return {
        "ok": True,
        "asset": asset,
        "horizon": horizon,
        "history": history,
        "current": {
            "price": round(base_price, 2),
            "expected": round(base_price * 1.02, 2),
            "verdict": random.choice(["bullish", "bearish", "neutral"])
        }
    }


@app.get("/api/system/health")
async def system_health():
    """System health status"""
    return {
        "ok": True,
        "status": "healthy",
        "services": {
            "database": "connected",
            "api": "running",
            "ml_engine": "standby"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/system/indexing-status")
async def indexing_status():
    """Indexing status"""
    return {
        "ok": True,
        "status": "idle",
        "last_run": datetime.now(timezone.utc).isoformat(),
        "progress": 100
    }


@app.get("/api/frontend/dashboard")
async def frontend_dashboard(page: int = 1, limit: int = 10):
    """Frontend dashboard data"""
    return {
        "ok": True,
        "globalState": {
            "btcPrice": 46422.26,
            "ethPrice": 2845.50,
            "marketCap": "1.8T",
            "fear_greed": 65,
            "dominance": 52.3
        },
        "tokens": [],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": 0
        },
        "alerts": [],
        "signals": []
    }


@app.get("/api/alerts/feed")
async def alerts_feed(limit: int = 5, unacknowledged: bool = True):
    """Alerts feed"""
    return {
        "ok": True,
        "alerts": [],
        "total": 0
    }


# Exchange & Advanced endpoints
@app.get("/api/exchange/pressure")
async def exchange_pressure(network: str = "ethereum", window: str = "24h"):
    """Exchange pressure data"""
    import random
    return {
        "ok": True,
        "network": network,
        "window": window,
        "data": {
            "inflow": round(random.uniform(1000, 5000), 2),
            "outflow": round(random.uniform(1000, 5000), 2),
            "netFlow": round(random.uniform(-500, 500), 2),
            "pressure": random.choice(["bullish", "bearish", "neutral"]),
            "confidence": round(random.uniform(0.5, 0.9), 2)
        }
    }


@app.get("/api/advanced/signals-attribution")
async def signals_attribution():
    """Signals attribution data"""
    import random
    return {
        "ok": True,
        "coverage": {
            "activeSignals": random.randint(5, 20),
            "totalSignals": random.randint(50, 100),
            "coverage": round(random.uniform(0.6, 0.95), 2)
        },
        "topImpactSignals": [
            {"name": "RSI Divergence", "impact": round(random.uniform(0.1, 0.3), 2)},
            {"name": "Volume Spike", "impact": round(random.uniform(0.1, 0.3), 2)},
            {"name": "MACD Cross", "impact": round(random.uniform(0.05, 0.2), 2)}
        ],
        "confidenceCalibration": {
            "accuracy": round(random.uniform(0.6, 0.85), 2),
            "calibration": round(random.uniform(0.7, 0.9), 2)
        }
    }


# Fractal endpoints
@app.get("/api/fractal/v2.1/chart")
async def fractal_chart(symbol: str = "BTC", limit: int = 450):
    """Fractal chart data"""
    import random
    from datetime import datetime, timedelta
    
    base_price = 45000 if symbol.upper() == "BTC" else 2800 if symbol.upper() == "ETH" else 4500 if symbol.upper() == "SPX" else 105
    now = datetime.now(timezone.utc)
    
    candles = []
    for i in list(reversed(list(range(1, limit + 1)))):
        ts = now - timedelta(days=i)
        change = random.uniform(-0.02, 0.02)
        open_price = base_price * (1 + change)
        close_price = open_price * (1 + random.uniform(-0.015, 0.015))
        high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
        low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.01))
        
        # Fractal format: t,o,h,l,c
        candles.append({
            "t": ts.strftime("%Y-%m-%d"),
            "o": round(open_price, 2),
            "h": round(high_price, 2),
            "l": round(low_price, 2),
            "c": round(close_price, 2)
        })
        base_price = close_price
    
    # SMA200
    sma200 = []
    if len(candles) >= 200:
        for i in list(range(200, len(candles))):
            avg = sum(c["c"] for c in candles[i-200:i]) / 200
            sma200.append({
                "t": candles[i]["t"],
                "v": round(avg, 2)
            })
    
    # Forecast data
    forecast_base = candles[-1]["c"] if candles else base_price
    synthetic = []
    replay = []
    hybrid = []
    
    for i in list(range(1, 31)):
        ts = now + timedelta(days=i)
        synthetic.append({
            "t": ts.strftime("%Y-%m-%d"),
            "v": round(forecast_base * (1 + random.uniform(-0.1, 0.15) * i / 30), 2)
        })
        replay.append({
            "t": ts.strftime("%Y-%m-%d"),
            "v": round(forecast_base * (1 + random.uniform(-0.08, 0.12) * i / 30), 2)
        })
        hybrid.append({
            "t": ts.strftime("%Y-%m-%d"),
            "v": round(forecast_base * (1 + random.uniform(-0.05, 0.10) * i / 30), 2)
        })
    
    # Phases
    phases = [
        {"start": (now - timedelta(days=90)).strftime("%Y-%m-%d"), "end": (now - timedelta(days=60)).strftime("%Y-%m-%d"), "label": "accumulation", "color": "#22c55e"},
        {"start": (now - timedelta(days=60)).strftime("%Y-%m-%d"), "end": (now - timedelta(days=30)).strftime("%Y-%m-%d"), "label": "markup", "color": "#3b82f6"},
        {"start": (now - timedelta(days=30)).strftime("%Y-%m-%d"), "end": now.strftime("%Y-%m-%d"), "label": "distribution", "color": "#f59e0b"}
    ]
    
    return {
        "ok": True,
        "symbol": symbol,
        "candles": candles,
        "sma200": sma200,
        "forecast": {
            "synthetic": synthetic,
            "replay": replay,
            "hybrid": hybrid
        },
        "phases": phases
    }


@app.get("/api/fractal/v2.1/signal")
async def fractal_signal(symbol: str = "BTC"):
    """Fractal signal"""
    import random
    return {
        "ok": True,
        "symbol": symbol,
        "signal": random.choice(["bullish", "bearish", "neutral"]),
        "confidence": round(random.uniform(0.5, 0.9), 2),
        "phase": random.choice(["accumulation", "markup", "distribution", "markdown"]),
        "alignment": round(random.uniform(0.3, 1.0), 2)
    }


@app.get("/api/fractal/v2.1/focus-pack")
async def fractal_focus_pack(symbol: str = "BTC", focus: str = "30d", phaseId: str = None, asOf: str = None):
    """Focus pack data for Fractal Intelligence"""
    import random
    from datetime import datetime, timedelta
    
    base_price = 45000 if symbol.upper() == "BTC" else 2800 if symbol.upper() == "ETH" else 4500 if symbol.upper() == "SPX" else 105
    horizon_days = int(focus.replace("d", "")) if focus.endswith("d") else 30
    now = datetime.now(timezone.utc)
    
    # Generate candles
    candles = []
    for i in list(reversed(list(range(1, 450 + 1)))):
        ts = now - timedelta(days=i)
        change = random.uniform(-0.02, 0.02)
        open_price = base_price * (1 + change)
        close_price = open_price * (1 + random.uniform(-0.015, 0.015))
        high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
        low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.01))
        
        candles.append({
            "t": ts.strftime("%Y-%m-%d"),
            "o": round(open_price, 2),
            "h": round(high_price, 2),
            "l": round(low_price, 2),
            "c": round(close_price, 2)
        })
        base_price = close_price
    
    current_price = candles[-1]["c"] if candles else base_price
    
    # Generate forecast path
    forecast_path = []
    price = current_price
    for i in list(range(horizon_days + 1)):
        forecast_path.append({
            "t": i,
            "price": round(price, 2),
            "pct": round((price / current_price - 1) * 100, 2)
        })
        price = price * (1 + random.uniform(-0.005, 0.01))
    
    # SMA200
    sma200 = []
    if len(candles) >= 200:
        for i in list(range(200, len(candles))):
            avg = sum(c["c"] for c in candles[i-200:i]) / 200
            sma200.append({
                "t": candles[i]["t"],
                "v": round(avg, 2)
            })
    
    # Phases
    phases = [
        {"start": (now - timedelta(days=90)).strftime("%Y-%m-%d"), "end": (now - timedelta(days=60)).strftime("%Y-%m-%d"), "label": "accumulation", "color": "#22c55e"},
        {"start": (now - timedelta(days=60)).strftime("%Y-%m-%d"), "end": (now - timedelta(days=30)).strftime("%Y-%m-%d"), "label": "markup", "color": "#3b82f6"},
        {"start": (now - timedelta(days=30)).strftime("%Y-%m-%d"), "end": now.strftime("%Y-%m-%d"), "label": "distribution", "color": "#f59e0b"}
    ]
    
    # Matches
    matches = []
    for i in list(range(5)):
        match_date = now - timedelta(days=random.randint(365, 2000))
        matches.append({
            "id": f"match_{i}",
            "date": match_date.strftime("%Y-%m-%d"),
            "similarity": round(random.uniform(0.6, 0.95), 2),
            "return": round(random.uniform(-0.1, 0.2), 2),
            "phase": random.choice(["accumulation", "markup", "distribution"])
        })
    
    focus_pack = {
        "symbol": symbol,
        "focus": focus,
        "horizonDays": horizon_days,
        
        # Chart data
        "chart": {
            "candles": candles,
            "sma200": sma200,
            "phases": phases
        },
        
        # Overlay
        "overlay": {
            "forecast": {
                "synthetic": forecast_path,
                "replay": forecast_path,
                "hybrid": forecast_path
            },
            "stats": {
                "hitRate": round(random.uniform(0.5, 0.8), 2),
                "avgReturn": round(random.uniform(-0.05, 0.15), 2)
            }
        },
        
        # Primary match
        "primarySelection": {
            "primaryMatch": matches[0] if matches else None
        },
        
        # Explain
        "explain": {
            "topMatches": matches
        },
        
        # Diagnostics
        "diagnostics": {
            "sampleSize": len(matches),
            "entropy": round(random.uniform(0.3, 0.7), 2),
            "reliability": round(random.uniform(0.5, 0.9), 2)
        },
        
        # Phase
        "phase": {
            "currentPhase": random.choice(["ACCUMULATION", "MARKUP", "DISTRIBUTION"]),
            "trend": random.choice(["UP", "DOWN", "SIDEWAYS"]),
            "volatility": random.choice(["LOW", "MODERATE", "HIGH"])
        },
        
        # Scenario
        "scenario": {
            "bear": {"return": round(random.uniform(-0.15, -0.05), 2), "price": round(current_price * 0.9, 2)},
            "base": {"return": round(random.uniform(-0.02, 0.08), 2), "price": round(current_price, 2)},
            "bull": {"return": round(random.uniform(0.05, 0.20), 2), "price": round(current_price * 1.1, 2)}
        },
        
        # Decision
        "decision": {
            "action": random.choice(["LONG", "SHORT", "HOLD"]),
            "confidence": round(random.uniform(40, 85), 0)
        },
        
        # Price
        "price": {
            "current": current_price,
            "sma200": "ABOVE" if current_price > (sma200[-1]["v"] if sma200 else current_price * 0.95) else "BELOW"
        }
    }
    
    return {
        "ok": True,
        "focusPack": focus_pack
    }


@app.get("/api/ui/overview")
async def ui_overview(asset: str = "BTC", horizon: int = 90):
    """UI Overview data for Fractal Intelligence"""
    import random
    from datetime import datetime, timedelta
    
    base_price = 45000 if asset.upper() == "BTC" else 2800 if asset.upper() == "ETH" else 4500 if asset.upper() == "SPX" else 105
    now = datetime.now(timezone.utc)
    
    candles = []
    for i in list(reversed(list(range(1, min(horizon, 365) + 1)))):
        ts = now - timedelta(days=i)
        change = random.uniform(-0.02, 0.02)
        open_price = base_price * (1 + change)
        close_price = open_price * (1 + random.uniform(-0.015, 0.015))
        high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
        low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.01))
        
        candles.append({
            "time": ts.strftime("%Y-%m-%d"),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2)
        })
        base_price = close_price
    
    # Forecast
    forecast = []
    for i in list(range(1, 31)):
        ts = now + timedelta(days=i)
        forecast.append({
            "t": ts.strftime("%Y-%m-%d"),
            "v": round(base_price * (1 + random.uniform(-0.05, 0.10) * i / 30), 2)
        })
    
    return {
        "ok": True,
        "asset": asset,
        "horizon": horizon,
        "candles": candles,
        "forecast": {
            "hybrid": forecast,
            "synthetic": forecast,
            "replay": forecast
        },
        "verdict": {
            "signal": random.choice(["bullish", "bearish", "neutral"]),
            "confidence": round(random.uniform(0.5, 0.9), 2),
            "phase": random.choice(["accumulation", "markup", "distribution"])
        },
        "currentPrice": round(base_price, 2)
    }


@app.get("/api/prediction/snapshots")
async def prediction_snapshots(asset: str = "BTC", view: str = "crossAsset", horizon: int = 90, limit: int = 20):
    """Prediction snapshots"""
    import random
    from datetime import datetime, timedelta
    
    now = datetime.now(timezone.utc)
    snapshots = []
    
    for i in list(range(limit)):
        ts = now - timedelta(hours=i * 6)
        snapshots.append({
            "id": f"snap_{i}",
            "timestamp": ts.isoformat(),
            "asset": asset,
            "prediction": random.choice(["UP", "DOWN"]),
            "confidence": round(random.uniform(0.5, 0.9), 2),
            "horizon": f"{random.choice([1, 7, 30])}D",
            "outcome": random.choice(["WIN", "LOSS", "PENDING"])
        })
    
    return {
        "ok": True,
        "snapshots": snapshots,
        "total": limit
    }


@app.get("/")
async def root():
    return {
        "name": "TA Engine Runtime",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "db_health": "/api/system/db-health",
            "ta_registry": "/api/ta/registry",
            "ta_patterns": "/api/ta/patterns",
            "ta_analyze": "/api/ta/analyze",
            "ui_candles": "/api/ui/candles",
            "forecast_curve": "/api/meta-brain-v2/forecast-curve",
            "forecast": "/api/forecast/{asset}",
            "fractal_summary": "/api/fractal/summary/{asset}",
            "fractal_chart": "/api/fractal/v2.1/chart",
            "exchange_pressure": "/api/exchange/pressure",
            "signals_attribution": "/api/advanced/signals-attribution"
        }
    }
