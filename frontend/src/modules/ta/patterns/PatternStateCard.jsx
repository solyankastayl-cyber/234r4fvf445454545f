/**
 * PatternStateCard
 * ================
 * 
 * Shows pattern state, triggers, and actionability.
 * This is the decision-grade UI for the pattern.
 */

import React from 'react';
import { getStateColor, getDirectionColor } from './patternRenderAdapter';

/**
 * @param {Object} props
 * @param {Object} props.pattern - Normalized pattern from adaptPatternV2
 */
export function PatternStateCard({ pattern }) {
  if (!pattern) {
    return (
      <div className="rounded-xl border border-neutral-800 bg-neutral-950/50 p-4">
        <div className="text-sm text-neutral-500">No pattern detected</div>
      </div>
    );
  }
  
  const stateColors = getStateColor(pattern.state);
  const dirColors = getDirectionColor(pattern.direction);
  
  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-950/80 backdrop-blur-sm p-4 space-y-4">
      {/* Header: Pattern + State */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xs text-neutral-500 uppercase tracking-wider mb-1">
            Primary Pattern
          </div>
          <div className="text-lg font-semibold text-white flex items-center gap-2">
            <span className={dirColors.text}>{dirColors.icon}</span>
            {pattern.title}
          </div>
        </div>
        
        <div className={`px-3 py-1.5 rounded-lg ${stateColors.bg} ${stateColors.border} border`}>
          <div className={`text-sm font-semibold ${stateColors.text}`}>
            {pattern.state}
          </div>
        </div>
      </div>
      
      {/* Summary */}
      {pattern.summary && (
        <div className="text-sm text-neutral-400 leading-relaxed">
          {pattern.summary}
        </div>
      )}
      
      {/* Stats Row */}
      <div className="flex flex-wrap gap-4 text-sm">
        <div className="flex items-center gap-1.5">
          <span className="text-neutral-500">Confidence:</span>
          <span className="text-white font-medium">
            {(pattern.confidence * 100).toFixed(0)}%
          </span>
        </div>
        
        <div className="flex items-center gap-1.5">
          <span className="text-neutral-500">Direction:</span>
          <span className={`font-medium ${dirColors.text}`}>
            {pattern.direction}
          </span>
        </div>
        
        <div className="flex items-center gap-1.5">
          <span className="text-neutral-500">Action:</span>
          <span className={`font-medium ${
            pattern.actionability === 'HIGH' ? 'text-green-400' :
            pattern.actionability === 'MEDIUM' ? 'text-yellow-400' :
            'text-neutral-400'
          }`}>
            {pattern.actionability}
          </span>
        </div>
        
        <div className="flex items-center gap-1.5">
          <span className="text-neutral-500">Tradeable:</span>
          <span className={pattern.tradeable ? 'text-green-400' : 'text-red-400'}>
            {pattern.tradeable ? 'Yes' : 'No'}
          </span>
        </div>
      </div>
      
      {/* Triggers - CRITICAL */}
      {(pattern.trigger.up || pattern.trigger.down) && (
        <div className="space-y-2">
          <div className="text-xs text-neutral-500 uppercase tracking-wider">
            Wait Conditions
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {pattern.trigger.up && (
              <div className="rounded-lg bg-green-500/10 border border-green-500/30 p-3">
                <div className="flex items-center gap-2 text-green-400 font-medium">
                  <span>▲</span>
                  <span>Breakout: {pattern.trigger.up.toLocaleString()}</span>
                </div>
                {pattern.trigger.upMessage && (
                  <div className="text-xs text-green-300/70 mt-1">
                    {pattern.trigger.upMessage}
                  </div>
                )}
              </div>
            )}
            
            {pattern.trigger.down && (
              <div className="rounded-lg bg-red-500/10 border border-red-500/30 p-3">
                <div className="flex items-center gap-2 text-red-400 font-medium">
                  <span>▼</span>
                  <span>Breakdown: {pattern.trigger.down.toLocaleString()}</span>
                </div>
                {pattern.trigger.downMessage && (
                  <div className="text-xs text-red-300/70 mt-1">
                    {pattern.trigger.downMessage}
                  </div>
                )}
              </div>
            )}
          </div>
          
          {pattern.trigger.invalidation && (
            <div className="rounded-lg bg-orange-500/10 border border-orange-500/30 p-2">
              <div className="flex items-center gap-2 text-orange-400 text-sm">
                <span>✗</span>
                <span>Invalidation: {pattern.trigger.invalidation.toLocaleString()}</span>
              </div>
            </div>
          )}
          
          {pattern.trigger.nearest && (
            <div className="text-xs text-neutral-500 mt-1">
              Nearest trigger: {pattern.trigger.nearest.direction?.toUpperCase()} at {pattern.trigger.nearest.level?.toLocaleString()} ({pattern.trigger.nearest.percent}% away)
            </div>
          )}
        </div>
      )}
      
      {/* Alternatives */}
      {pattern.alternatives && pattern.alternatives.length > 0 && (
        <div className="pt-2 border-t border-neutral-800">
          <div className="text-xs text-neutral-500 mb-2">Alternatives:</div>
          <div className="flex flex-wrap gap-2">
            {pattern.alternatives.map((alt, i) => (
              <span 
                key={i}
                className={`text-xs px-2 py-1 rounded ${
                  alt.bias === 'bullish' ? 'bg-green-500/10 text-green-400' :
                  alt.bias === 'bearish' ? 'bg-red-500/10 text-red-400' :
                  'bg-neutral-500/10 text-neutral-400'
                }`}
              >
                {alt.type.replace(/_/g, ' ')} ({(alt.confidence * 100).toFixed(0)}%)
              </span>
            ))}
          </div>
        </div>
      )}
      
      {/* Regime Context */}
      {pattern.regimeContext && (
        <div className="pt-2 border-t border-neutral-800 text-xs text-neutral-500">
          Regime: {pattern.regimeContext.regime} | Trend: {pattern.regimeContext.trend}
        </div>
      )}
    </div>
  );
}

export default PatternStateCard;
