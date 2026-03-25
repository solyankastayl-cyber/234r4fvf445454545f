/**
 * PatternSVGOverlay.jsx — TA LAYERS BASED RENDERING
 * 
 * PRIORITY:
 * 1. active_range (главный слой)
 * 2. strict pattern (double top, H&S)
 * 3. loose pattern (пунктир)
 * 4. structure only
 * 
 * Uses ta_layers as source of truth, NOT pattern_render_contract
 */

import React, { useEffect, useState, useCallback } from 'react';

const PatternSVGOverlay = ({ chart, priceSeries, pattern, renderContract, data }) => {
  const [svgElements, setSvgElements] = useState([]);
  
  const buildElements = useCallback(() => {
    console.log('[PatternSVGOverlay] buildElements called', { 
      hasChart: !!chart, 
      hasPriceSeries: !!priceSeries, 
      hasData: !!data,
      hasRenderContract: !!renderContract 
    });
    
    if (!chart || !priceSeries) {
      console.log('[PatternSVGOverlay] Missing chart or priceSeries');
      return [];
    }
    
    try {
      const timeScale = chart.timeScale();
      if (!timeScale) {
        console.log('[PatternSVGOverlay] No timeScale');
        return [];
      }
      
      const visibleRange = timeScale.getVisibleRange();
      if (!visibleRange) {
        console.log('[PatternSVGOverlay] No visibleRange');
        return [];
      }
      
      console.log('[PatternSVGOverlay] Data received:', JSON.stringify({
        data: data ? Object.keys(data) : null,
        active_range: data?.active_range,
        ta_layers: data?.ta_layers ? Object.keys(data.ta_layers) : null,
        scenarios: data?.ta_layers?.scenarios,
        probability: data?.ta_layers?.probability
      }, null, 2));
      
      const normalizeTime = (t) => {
        if (!t) return null;
        // FIX: ms → sec
        return t > 9999999999 ? Math.floor(t / 1000) : t;
      };
      
      const toX = (time) => {
        const normalized = normalizeTime(time);
        if (!normalized) return null;
        const x = timeScale.timeToCoordinate(normalized);
        return Number.isFinite(x) ? x : null;
      };
      
      const toY = (price) => {
        if (price === null || price === undefined) return null;
        try {
          const y = priceSeries.priceToCoordinate(price);
          return Number.isFinite(y) ? y : null;
        } catch {
          return null;
        }
      };
      
      // ═══════════════════════════════════════════════════════════════
      // PRIORITY 1: ACTIVE RANGE (from ta_layers) + BREAKOUT TARGETS
      // ═══════════════════════════════════════════════════════════════
      const activeRange = data?.active_range || data?.ta_layers?.active_range;
      const scenarios = data?.ta_layers?.scenarios;
      const probability = data?.ta_layers?.probability;
      
      if (activeRange && activeRange.top && activeRange.bottom) {
        return renderRange(activeRange, toX, toY, visibleRange, scenarios, probability);
      }
      
      // ═══════════════════════════════════════════════════════════════
      // PRIORITY 2: TA_LAYERS PATTERN (strict mode)
      // ═══════════════════════════════════════════════════════════════
      const taPattern = data?.ta_layers?.pattern;
      
      if (taPattern && taPattern.type && taPattern.confidence > 0.5) {
        const patternType = (taPattern.type || '').toLowerCase();
        
        // Use meta from pattern or renderContract
        const meta = taPattern.meta || renderContract?.meta || {};
        
        if (patternType === 'double_top' || patternType === 'double_bottom') {
          return renderDoublePattern(patternType, renderContract, meta, toX, toY);
        }
        
        if (patternType.includes('triangle') || patternType.includes('wedge')) {
          return renderTriangle(meta, toX, toY);
        }
      }
      
      // ═══════════════════════════════════════════════════════════════
      // PRIORITY 3: RANGE from regime (if ta_layers says regime=range)
      // ═══════════════════════════════════════════════════════════════
      const regime = data?.ta_layers?.regime;
      
      if (regime?.regime === 'range' && regime?.range) {
        return renderRange(regime.range, toX, toY, visibleRange, scenarios, probability);
      }
      
      // ═══════════════════════════════════════════════════════════════
      // PRIORITY 4: FALLBACK to renderContract (legacy)
      // ═══════════════════════════════════════════════════════════════
      if (renderContract && renderContract.display_approved) {
        const patternType = (renderContract.type || '').toLowerCase();
        const meta = renderContract.meta || {};
        
        if (patternType.includes('range')) {
          const rangeData = {
            top: meta.resistance || meta.boundaries?.upper?.y1,
            bottom: meta.support || meta.boundaries?.lower?.y1,
            start_time: meta.boundaries?.upper?.x1 || meta.boundaries?.lower?.x1,
            end_time: visibleRange.to,
            forward_time: visibleRange.to + (visibleRange.to - visibleRange.from) * 0.3,
          };
          return renderRange(rangeData, toX, toY, visibleRange, scenarios, probability);
        }
        
        if (patternType === 'double_top' || patternType === 'double_bottom') {
          return renderDoublePattern(patternType, renderContract, meta, toX, toY);
        }
        
        if (patternType.includes('triangle') || patternType.includes('wedge')) {
          return renderTriangle(meta, toX, toY);
        }
      }
      
      return [];
      
    } catch (err) {
      console.error('[PatternSVGOverlay] Error:', err);
      return [];
    }
  }, [chart, priceSeries, renderContract, data]);
  
  useEffect(() => {
    if (!chart || !priceSeries) {
      setSvgElements([]);
      return;
    }
    
    const update = () => setSvgElements(buildElements());
    update();
    
    const timeScale = chart.timeScale();
    if (timeScale) timeScale.subscribeVisibleTimeRangeChange(update);
    chart.subscribeCrosshairMove(update);
    
    return () => {
      if (timeScale) timeScale.unsubscribeVisibleTimeRangeChange(update);
      chart.unsubscribeCrosshairMove(update);
    };
  }, [chart, priceSeries, renderContract, data, buildElements]);
  
  if (!svgElements || svgElements.length === 0) return null;
  
  return (
    <svg
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        overflow: 'visible',
        zIndex: 50,
      }}
    >
      {svgElements}
    </svg>
  );
};

// ═══════════════════════════════════════════════════════════════
// 🟦 RANGE RENDERING — CLEAN MINIMAL UI
// ═══════════════════════════════════════════════════════════════
// PRINCIPLE: 1 screen = 1 idea
// Show ONLY: Range box + Support/Resistance + 2 Scenarios
// ═══════════════════════════════════════════════════════════════
function renderRange(range, toX, toY, visibleRange, scenarios, probability) {
  const elements = [];
  
  const top = range.top;
  const bottom = range.bottom;
  const startTime = range.start_time || range.left_boundary_time || range.left_time;
  
  let endTime = range.forward_time || range.end_time || range.right_time;
  if (visibleRange && endTime) {
    const visibleEnd = visibleRange.to;
    const extendedEnd = visibleEnd + (visibleEnd - visibleRange.from) * 0.5;
    if (endTime > extendedEnd) {
      endTime = extendedEnd;
    }
  }
  
  const left = toX(startTime);
  let right = toX(endTime);
  if (!right && visibleRange) {
    right = toX(visibleRange.to);
    if (!right) right = 1400;
  }
  
  const yTop = toY(top);
  const yBottom = toY(bottom);
  
  if (!yTop || !yBottom) return [];
  
  const effectiveLeft = Math.max(left || 0, 0);
  const effectiveRight = Math.max(right || 1400, effectiveLeft + 100);
  const width = Math.max(effectiveRight - effectiveLeft, 100);
  const rangeHeight = Math.abs(yBottom - yTop);
  const yStart = Math.min(yTop, yBottom);
  
  // Scenarios
  const breakUp = scenarios?.break_up;
  const breakDown = scenarios?.break_down;
  
  // ═══════════════════════════════════════════════════════════════
  // 1. RANGE BOX — subtle fill, clean
  // ═══════════════════════════════════════════════════════════════
  elements.push(
    <rect
      key="range-fill"
      x={effectiveLeft}
      y={yStart}
      width={width}
      height={rangeHeight}
      fill="rgba(100, 116, 139, 0.06)"
      stroke="none"
    />
  );
  
  // ═══════════════════════════════════════════════════════════════
  // 2. RESISTANCE LINE — clean solid line
  // ═══════════════════════════════════════════════════════════════
  elements.push(
    <line
      key="resistance"
      x1={effectiveLeft}
      y1={yTop}
      x2={effectiveRight}
      y2={yTop}
      stroke="#ef4444"
      strokeWidth={2}
    />
  );
  
  // Resistance label
  elements.push(
    <text
      key="resistance-label"
      x={effectiveRight - 80}
      y={yTop - 6}
      fill="#ef4444"
      fontSize="11"
      fontWeight="600"
    >
      R {top?.toFixed(0)}
    </text>
  );
  
  // ═══════════════════════════════════════════════════════════════
  // 3. SUPPORT LINE — clean solid line
  // ═══════════════════════════════════════════════════════════════
  elements.push(
    <line
      key="support"
      x1={effectiveLeft}
      y1={yBottom}
      x2={effectiveRight}
      y2={yBottom}
      stroke="#22c55e"
      strokeWidth={2}
    />
  );
  
  // Support label
  elements.push(
    <text
      key="support-label"
      x={effectiveRight - 80}
      y={yBottom + 14}
      fill="#22c55e"
      fontSize="11"
      fontWeight="600"
    >
      S {bottom?.toFixed(0)}
    </text>
  );
  
  // ═══════════════════════════════════════════════════════════════
  // 4. SCENARIOS — simple arrows at edge showing direction
  // ═══════════════════════════════════════════════════════════════
  const scenarioX = effectiveRight - 20;
  
  // Break UP scenario arrow
  if (breakUp?.target) {
    const arrowY = yTop - 25;
    elements.push(
      <g key="scenario-up">
        {/* Arrow pointing up */}
        <polygon
          points={`${scenarioX},${arrowY} ${scenarioX-6},${arrowY+10} ${scenarioX+6},${arrowY+10}`}
          fill="#22c55e"
        />
        {/* Target price */}
        <text
          x={scenarioX + 12}
          y={arrowY + 8}
          fill="#22c55e"
          fontSize="10"
          fontWeight="600"
        >
          → {breakUp.target?.toFixed(0)}
        </text>
      </g>
    );
  }
  
  // Break DOWN scenario arrow
  if (breakDown?.target) {
    const arrowY = yBottom + 25;
    elements.push(
      <g key="scenario-down">
        {/* Arrow pointing down */}
        <polygon
          points={`${scenarioX},${arrowY} ${scenarioX-6},${arrowY-10} ${scenarioX+6},${arrowY-10}`}
          fill="#ef4444"
        />
        {/* Target price */}
        <text
          x={scenarioX + 12}
          y={arrowY - 2}
          fill="#ef4444"
          fontSize="10"
          fontWeight="600"
        >
          → {breakDown.target?.toFixed(0)}
        </text>
      </g>
    );
  }
  
  return elements;
}

// ═══════════════════════════════════════════════════════════════
// 🔺 DOUBLE TOP/BOTTOM RENDERING
// ═══════════════════════════════════════════════════════════════
function renderDoublePattern(patternType, renderContract, meta, toX, toY) {
  const isTop = patternType === 'double_top';
  const anchors = renderContract?.anchors || {};
  
  let p1, valley, p2;
  let p2IsProjected = false;
  
  if (anchors.p1 && anchors.p2 && anchors.valley) {
    p1 = anchors.p1;
    p2 = anchors.p2;
    valley = anchors.valley;
  } else if (anchors.p1 && anchors.valley) {
    p1 = anchors.p1;
    valley = anchors.valley;
    const timeDiff = valley.time - p1.time;
    p2 = {
      time: valley.time + timeDiff,
      price: p1.price
    };
    p2IsProjected = true;
  } else {
    return [];
  }
  
  if (!p1 || !valley) return [];
  
  if (!p2) {
    const timeDiff = valley.time - p1.time;
    p2 = {
      time: valley.time + timeDiff,
      price: p1.price
    };
    p2IsProjected = true;
  }
  
  const peakPrice = (p1.price + p2.price) / 2;
  const necklinePrice = valley.price;
  const height = Math.abs(peakPrice - necklinePrice);
  const targetPrice = isTop ? necklinePrice - height : necklinePrice + height;
  
  const x1 = toX(p1.time);
  const y1 = toY(peakPrice);
  const xV = toX(valley.time);
  const yV = toY(necklinePrice);
  const x2 = toX(p2.time);
  const y2 = toY(peakPrice);
  const yTarget = toY(targetPrice);
  
  if (!x1 || !y1 || !xV || !yV || !x2 || !y2) {
    return [];
  }
  
  const elements = [];
  const mainColor = '#000000';
  const projectedColor = '#666666';
  
  // M-shape
  elements.push(
    <line
      key="left-side"
      x1={x1}
      y1={y1}
      x2={xV}
      y2={yV}
      stroke={mainColor}
      strokeWidth={2}
      strokeLinecap="round"
    />
  );
  
  elements.push(
    <line
      key="right-side"
      x1={xV}
      y1={yV}
      x2={x2}
      y2={y2}
      stroke={p2IsProjected ? projectedColor : mainColor}
      strokeWidth={2}
      strokeLinecap="round"
      strokeDasharray={p2IsProjected ? "4 3" : "none"}
    />
  );
  
  // Neckline
  elements.push(
    <line
      key="neckline"
      x1={x1}
      y1={yV}
      x2={x2 + 50}
      y2={yV}
      stroke="cyan"
      strokeWidth={1}
      strokeDasharray="4 2"
    />
  );
  
  // Target arrow
  if (yTarget) {
    const arrowStartX = x2 + 10;
    const arrowStartY = yV;
    const arrowEndX = x2 + 50;
    const arrowEndY = yTarget;
    
    elements.push(
      <line
        key="prediction"
        x1={arrowStartX}
        y1={arrowStartY}
        x2={arrowEndX}
        y2={arrowEndY}
        stroke={mainColor}
        strokeWidth={2}
      />
    );
    
    // Arrow head
    const angle = Math.atan2(arrowEndY - arrowStartY, arrowEndX - arrowStartX);
    const headLen = 8;
    const h1X = arrowEndX - headLen * Math.cos(angle - Math.PI / 6);
    const h1Y = arrowEndY - headLen * Math.sin(angle - Math.PI / 6);
    const h2X = arrowEndX - headLen * Math.cos(angle + Math.PI / 6);
    const h2Y = arrowEndY - headLen * Math.sin(angle + Math.PI / 6);
    
    elements.push(
      <polygon
        key="arrow-head"
        points={`${arrowEndX},${arrowEndY} ${h1X},${h1Y} ${h2X},${h2Y}`}
        fill={mainColor}
      />
    );
    
    elements.push(
      <text
        key="target"
        x={arrowEndX + 5}
        y={arrowEndY + 4}
        fill={mainColor}
        fontSize="11"
        fontWeight="bold"
      >
        {targetPrice.toFixed(0)}
      </text>
    );
  }
  
  // Points
  elements.push(<circle key="p1" cx={x1} cy={y1} r={4} fill={mainColor} />);
  elements.push(
    <text key="p1-label" x={x1} y={y1 - 8} fill={mainColor} fontSize="10" fontWeight="bold" textAnchor="middle">P1</text>
  );
  
  elements.push(
    <circle 
      key="p2" 
      cx={x2} 
      cy={y2} 
      r={4} 
      fill={p2IsProjected ? "none" : mainColor}
      stroke={mainColor}
      strokeWidth={p2IsProjected ? 2 : 0}
    />
  );
  elements.push(
    <text key="p2-label" x={x2} y={y2 - 8} fill={projectedColor} fontSize="10" fontWeight="bold" textAnchor="middle">
      P2{p2IsProjected ? "?" : ""}
    </text>
  );
  
  return elements;
}

// ═══════════════════════════════════════════════════════════════
// 🔺 TRIANGLE/WEDGE RENDERING
// ═══════════════════════════════════════════════════════════════
function renderTriangle(meta, toX, toY) {
  const boundaries = meta.boundaries || {};
  const upper = boundaries.upper;
  const lower = boundaries.lower;
  
  if (!upper || !lower) return [];
  
  const x1u = toX(upper.x1);
  const y1u = toY(upper.y1);
  const x2u = toX(upper.x2);
  const y2u = toY(upper.y2);
  const x1l = toX(lower.x1);
  const y1l = toY(lower.y1);
  const x2l = toX(lower.x2);
  const y2l = toY(lower.y2);
  
  if (!x1u || !y1u || !x2u || !y2u || !x1l || !y1l || !x2l || !y2l) {
    return [];
  }
  
  return [
    <line key="upper" x1={x1u} y1={y1u} x2={x2u} y2={y2u} stroke="#000000" strokeWidth={2} />,
    <line key="lower" x1={x1l} y1={y1l} x2={x2l} y2={y2l} stroke="#000000" strokeWidth={2} />
  ];
}

export default PatternSVGOverlay;
