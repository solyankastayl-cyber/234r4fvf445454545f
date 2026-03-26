/**
 * ResearchView — Technical Analysis Research Terminal
 * ====================================================
 * 
 * Uses Setup API to display:
 * 1. Full-width chart with patterns, levels, bias
 * 2. Pattern Activation Layer
 * 3. Deep Analysis Blocks
 * 4. Save Idea functionality
 */

import React, { useState, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import { 
  Search, 
  RefreshCw, 
  Share2, 
  Camera, 
  Bookmark,
  Loader2,
  AlertTriangle,
  ChevronDown,
  BarChart2,
  LineChart,
  Eye,
  EyeOff,
  Settings2,
  Triangle,
  Layers,
  TrendingUp,
  Target
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════
// TA VISUALIZATION — RenderPlan + Renderers (moved from Chart Lab)
// ═══════════════════════════════════════════════════════════════
import { useRenderPlan } from '../../../store/marketStore';
import { RenderPlanOverlay } from '../renderers';

import ResearchChart from '../components/ResearchChart';
import PatternActivationLayer from '../components/PatternActivationLayer';
import DeepAnalysisBlocks from '../components/DeepAnalysisBlocks';
import MarketContextBar from '../components/MarketContextBar';
import ScenariosBlock from '../components/ScenariosBlock';
import PatternsBlock from '../components/PatternsBlock';
import TALayersPanel from '../components/TALayersPanel';
import { TAExplorerPanel } from '../components/ta-explorer';
import ConfidenceExplanation from '../components/ConfidenceExplanation';
import ExplanationPanel from '../components/ExplanationPanel';
import IndicatorPanes from '../components/IndicatorPanes';
import IndicatorControlBar from '../components/IndicatorControlBar';
import ConfluenceMatrix from '../components/ConfluenceMatrix';
import IndicatorSelector from '../components/IndicatorSelector';
import ViewModeSelector from '../components/ViewModeSelector';
import TAContextPanel from '../components/TAContextPanel';
import RenderPlanReasons from '../components/RenderPlanReasons';
import TACompositionPanel from '../components/TACompositionPanel';
import UnifiedSetupPanel from '../components/UnifiedSetupPanel';
import MTFHeaderPanel from '../components/MTFHeaderPanel';
import ExecutionPanel from '../components/ExecutionPanel';
import PatternHintCard from '../components/PatternHintCard';
import { 
  computeVisibility, 
  getLayerLimits, 
  applyLimits, 
  getLayerStyle,
  LAYER_PRIORITY,
  VISUAL_PRIORITY 
} from '../engine/GraphVisibilityEngine';
import setupService from '../../../services/setupService';
import { buildNarrative, NarrativeSummary } from '../../../components/chart-engine/narrative';
import StoryLine from '../components/StoryLine';

// ════════════════════════════════════════════════════════════════
// PATTERN V2 — New unified pattern detection system
// ════════════════════════════════════════════════════════════════
import { usePatternV2, PatternStateCard } from '../../ta/patterns';

// ════════════════════════════════════════════════════════════════
// CONFLUENCE ENGINE — TA Decision Logic (NEW!)
// ════════════════════════════════════════════════════════════════
import { buildConfluence, getLayerVisibility } from '../utils/confluenceEngine';
import { buildTradeSetup } from '../utils/setupGenerator';

// ============================================
// STYLED COMPONENTS
// ============================================

const Container = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f8fafc;
  overflow-y: auto;
`;

const TopBar = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #ffffff;
  border-bottom: 1px solid #eef1f5;
  flex-wrap: wrap;
  gap: 12px;
`;

const ControlsLeft = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const ControlsRight = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`;

const SearchWrapper = styled.div`
  position: relative;
`;

const SearchInput = styled.input`
  width: 160px;
  padding: 10px 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
  letter-spacing: 0.5px;
  
  &:focus {
    outline: none;
    border-color: #05A584;
    background: #ffffff;
  }
  
  &::placeholder {
    color: #94a3b8;
    font-weight: 500;
  }
`;

const SymbolDropdown = styled.div`
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  z-index: 100;
  max-height: 200px;
  overflow-y: auto;
`;

const SymbolOption = styled.button`
  width: 100%;
  padding: 10px 12px;
  text-align: left;
  border: none;
  background: ${({ $active }) => $active ? '#f0f9ff' : 'transparent'};
  font-size: 13px;
  font-weight: 500;
  color: #0f172a;
  cursor: pointer;
  
  &:hover {
    background: #f8fafc;
  }
`;

const TfGroup = styled.div`
  display: flex;
  gap: 2px;
  background: #f1f5f9;
  padding: 3px;
  border-radius: 8px;
`;

const TfButton = styled.button`
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  border: none;
  background: ${({ $active }) => $active ? '#ffffff' : 'transparent'};
  color: ${({ $active }) => $active ? '#0f172a' : '#64748b'};
  cursor: pointer;
  box-shadow: ${({ $active }) => $active ? '0 1px 3px rgba(0,0,0,0.08)' : 'none'};
  transition: all 0.15s ease;
  
  &:hover {
    color: #0f172a;
  }
`;

const ChartTypeGroup = styled.div`
  display: flex;
  gap: 2px;
  background: #f1f5f9;
  padding: 3px;
  border-radius: 8px;
`;

const ChartTypeBtn = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px 10px;
  border-radius: 6px;
  border: none;
  background: ${({ $active }) => $active ? '#ffffff' : 'transparent'};
  color: ${({ $active }) => $active ? '#0f172a' : '#64748b'};
  cursor: pointer;
  box-shadow: ${({ $active }) => $active ? '0 1px 3px rgba(0,0,0,0.08)' : 'none'};
  
  svg {
    width: 16px;
    height: 16px;
  }
  
  &:hover {
    color: #0f172a;
  }
`;

const ViewModeWrapper = styled.div`
  position: relative;
`;

const ViewModeButton = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #0f172a;
  cursor: pointer;
  
  &:hover {
    border-color: #cbd5e1;
  }
  
  svg {
    width: 14px;
    height: 14px;
    color: #94a3b8;
  }
`;

const ViewModeDropdown = styled.div`
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 4px;
  min-width: 140px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 50;
  overflow: hidden;
`;

const ViewModeOption = styled.button`
  display: block;
  width: 100%;
  padding: 10px 14px;
  background: ${({ $active }) => $active ? '#f8fafc' : '#ffffff'};
  border: none;
  text-align: left;
  font-size: 13px;
  font-weight: ${({ $active }) => $active ? '600' : '500'};
  color: #0f172a;
  cursor: pointer;
  
  &:hover {
    background: #f1f5f9;
  }
`;

const ActionBtn = styled.button`
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  
  svg {
    width: 14px;
    height: 14px;
  }
  
  &:hover {
    border-color: #3b82f6;
    color: #3b82f6;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  &.primary {
    background: #3b82f6;
    border-color: #3b82f6;
    color: #ffffff;
    
    &:hover {
      background: #2563eb;
    }
  }
  
  &.loading svg {
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

// LayerToggles and LayerToggleBtn removed - using ViewModeSelector instead

const MainContent = styled.div`
  flex: 1;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

const ChartSection = styled.div`
  background: #ffffff;
  border: 1px solid #eef1f5;
  border-radius: 12px;
  overflow: hidden;
`;

const ErrorBanner = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 13px;
  
  svg {
    flex-shrink: 0;
  }
`;

const LoadingOverlay = styled.div`
  position: absolute;
  inset: 0;
  background: rgba(255,255,255,0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  z-index: 10;
  
  svg {
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

const SuccessToast = styled.div`
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 12px 20px;
  background: #05A584;
  color: #ffffff;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(5, 165, 132, 0.3);
  z-index: 1000;
  animation: slideIn 0.3s ease;
  
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;

const DebugPanel = styled.div`
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  padding: 16px 20px;
  margin: 16px 0;
  font-family: 'Gilroy', 'Inter', -apple-system, sans-serif;
  
  .debug-title {
    font-weight: 700;
    font-size: 11px;
    color: #64748b;
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  
  .debug-row {
    display: flex;
    gap: 32px;
    padding: 8px 0;
    border-bottom: 1px solid #f1f5f9;
    
    &:last-child {
      border-bottom: none;
    }
  }
  
  .debug-label {
    min-width: 100px;
    font-size: 12px;
    font-weight: 500;
    color: #94a3b8;
  }
  
  .debug-value {
    font-size: 13px;
    font-weight: 600;
    color: #0f172a;
    
    &.bullish { color: #05A584; }
    &.bearish { color: #ef4444; }
    &.neutral { color: #64748b; }
  }
`;

// New Decision Layer UI Components
const BottomGrid = styled.div`
  display: flex;
  gap: 12px;
  margin-top: 12px;
  
  & > * {
    flex: 1;
    min-width: 0;
  }
  
  @media (max-width: 900px) {
    flex-direction: column;
  }
`;

const SubChartControls = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
  padding: 8px 16px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  margin: 0 0 8px 0;
  
  /* Overlay toggle section */
  .overlay-section {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    background: #f8fafc;
    border-radius: 6px;
  }
  
  .section-label {
    font-size: 10px;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-right: 4px;
  }
`;

const ControlDivider = styled.div`
  width: 1px;
  height: 24px;
  background: #e2e8f0;
  margin: 0 8px;
`;

const CollapsibleButton = styled.button`
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  background: ${({ $active }) => $active ? '#0f172a' : '#f8fafc'};
  border: 1px solid ${({ $active }) => $active ? '#0f172a' : '#e2e8f0'};
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  color: ${({ $active }) => $active ? '#ffffff' : '#64748b'};
  cursor: pointer;
  transition: all 0.15s ease;
  
  &:hover {
    border-color: ${({ $active }) => $active ? '#1e293b' : '#cbd5e1'};
    background: ${({ $active }) => $active ? '#1e293b' : '#f1f5f9'};
  }
  
  svg {
    width: 13px;
    height: 13px;
    opacity: ${({ $active }) => $active ? 1 : 0.6};
  }
  
  /* Status indicator dot */
  &::after {
    content: '';
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: ${({ $active }) => $active ? '#22c55e' : 'transparent'};
    margin-left: 4px;
  }
`;

const BottomSection = styled.div`
  margin-top: 12px;
`;

// ============================================
// CONSTANTS
// ============================================

const SYMBOLS = [
  'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT',
  'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'MATICUSDT',
  'LINKUSDT', 'UNIUSDT', 'ATOMUSDT', 'LTCUSDT', 'ETCUSDT',
  'FILUSDT', 'APTUSDT', 'ARBUSDT', 'OPUSDT', 'NEARUSDT',
  'INJUSDT', 'SUIUSDT', 'AAVEUSDT', 'MKRUSDT', 'CRVUSDT',
  'TONUSDT', 'SEIUSDT', 'TIAUSDT', 'JUPUSDT', 'WIFUSDT'
];
const TIMEFRAMES = ['4H', '1D', '7D', '30D', '180D', '1Y'];
const MTF_TIMEFRAMES = ['1D', '4H', '1H']; // Available MTF timeframes

// TF Display Names — human-readable labels
const TF_DISPLAY_NAMES = {
  '4H': '4H',
  '1D': '1D',
  '7D': '7D',
  '30D': '1M',   // 30D → 1M for clarity
  '180D': '6M',  // 180D → 6M for clarity
  '1Y': '1Y',
};

// ============================================
// COMPONENT
// ============================================

const ResearchView = () => {
  // ═══════════════════════════════════════════════════════════════
  // RESEARCH STATE — TA-specific (isolated from Chart Lab)
  // ═══════════════════════════════════════════════════════════════
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [timeframe, setTimeframe] = useState('1D');
  const [selectedTF, setSelectedTF] = useState('4H');
  const [chartType, setChartType] = useState('candles');
  const [viewMode, setViewMode] = useState('auto');
  const [showViewModeDropdown, setShowViewModeDropdown] = useState(false);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);
  
  // ═══════════════════════════════════════════════════════════════
  // TA OVERLAY STATE — moved from Chart Lab (RESEARCH EXCLUSIVE)
  // ═══════════════════════════════════════════════════════════════
  const [showTAOverlay, setShowTAOverlay] = useState(false);  // OFF by default - reduces noise
  
  // Hook into global render plan store for TA visualization
  const { renderPlan: globalRenderPlan, loading: renderPlanLoading, refresh: refreshRenderPlan } = useRenderPlan();
  
  // Collapsible panels state — toggles overlay visibility on chart
  // ALL OFF by default to reduce visual noise - user clicks to enable
  const [showFibonacciOverlay, setShowFibonacciOverlay] = useState(false);
  const [showPatternOverlay, setShowPatternOverlay] = useState(true);  // V4: Default ON for anchor-based patterns
  const [showSetupOverlay, setShowSetupOverlay] = useState(false);
  
  // PATTERN VIEW MODE — isolates pattern for readability
  // When true: hide structure, levels, indicators — show only candles + pattern
  const [patternViewMode, setPatternViewMode] = useState(false);
  
  // Data - NEW: MTF data structure
  const [tfMap, setTfMap] = useState({});
  const [mtfContext, setMtfContext] = useState(null);
  const [setupData, setSetupData] = useState(null);
  const [candles, setCandles] = useState([]);
  
  // Active elements for pattern activation
  const [activeElements, setActiveElements] = useState({});
  
  // Active pattern for switching between primary/alternatives
  const [activePatternId, setActivePatternId] = useState('primary');
  
  // Pattern index for V4 render contract switching (0 = primary, 1+ = alternatives)
  const [patternIndex, setPatternIndex] = useState(0);
  
  // Layer visibility now controlled by viewMode through layerVisibilityComputed
  // Removed manual layerVisibility state to avoid duplication
  
  // Indicator selection state (max 2 overlays, max 2 panes)
  const [selectedOverlays, setSelectedOverlays] = useState(['ema_20', 'ema_50']);
  const [selectedPanes, setSelectedPanes] = useState(['rsi', 'macd']);
  
  // Active indicators toggle (for pane visibility)
  const [activeIndicators, setActiveIndicators] = useState({ rsi: false, macd: false });
  
  // ═══════════════════════════════════════════════════════════════
  // PATTERN V2 — Unified detection with render contract & triggers
  // ═══════════════════════════════════════════════════════════════
  const baseSymbol = symbol.replace('USDT', '');
  const { pattern: patternV2, loading: patternV2Loading } = usePatternV2(baseSymbol, selectedTF);
  
  const handleIndicatorToggle = useCallback((indicator) => {
    setActiveIndicators(prev => ({
      ...prev,
      [indicator]: !prev[indicator]
    }));
  }, []);

  // Fetch MTF data from per-timeframe pipeline
  // CRITICAL: Fetch ALL timeframes at once, not one by one
  const fetchSetup = useCallback(async () => {
    console.log('[MTF] Starting fetch for ALL timeframes...');
    setLoading(true);
    setError(null);
    
    try {
      // Extract base symbol (BTC from BTCUSDT)
      const baseSymbol = symbol.replace('USDT', '');
      
      // CRITICAL: Request ALL TIMEFRAMES at once (was MTF_TIMEFRAMES, now TIMEFRAMES)
      const allTFs = TIMEFRAMES.join(',');
      const url = `/api/ta-engine/mtf/${baseSymbol}?timeframes=${allTFs}`;
      console.log('[MTF] Fetching ALL TFs:', url);
      
      // Add timeout controller - increased to 35s for MTF endpoint
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 35000);
      
      // Fetch MTF data
      const response = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);
      
      console.log('[MTF] Response status:', response.status);
      
      if (!response.ok) {
        throw new Error('Failed to fetch MTF analysis');
      }
      
      const data = await response.json();
      const tfKeys = Object.keys(data.tf_map || {});
      console.log('[MTF] Data received, tf_map keys:', tfKeys);
      
      // Store ALL MTF data in cache
      setTfMap(data.tf_map || {});
      setMtfContext(data.mtf_context || null);
      
      // Set active TF data as setupData for compatibility
      const activeTFData = data.tf_map?.[selectedTF] || {};
      setSetupData(activeTFData);
      setCandles(activeTFData.candles || []);
      setActivePatternId('primary');
      
      // 🔥 CRITICAL LOG: Verify each TF has different render_plan
      tfKeys.forEach(tf => {
        const tfData = data.tf_map[tf];
        const rp = tfData?.render_plan;
        console.log(`[MTF] TF=${tf}: candles=${tfData?.candles?.length}, swings=${rp?.structure?.swings?.length}, levels=${rp?.levels?.length}`);
      });
      
    } catch (err) {
      if (err.name === 'AbortError') {
        console.error('[MTF] Fetch timeout');
        setError('Analysis timeout - please try again');
      } else {
        console.error('[MTF] Fetch error:', err);
        setError(err.message || 'Failed to load analysis');
      }
    } finally {
      setLoading(false);
      console.log('[MTF] Fetch complete');
    }
  }, [symbol, selectedTF]);

  // Update setupData when selectedTF changes — use cached data
  useEffect(() => {
    if (tfMap[selectedTF]) {
      // Data already cached — use it IMMEDIATELY
      const tfData = tfMap[selectedTF];
      setSetupData(tfData);
      setCandles(tfData.candles || []);
      
      // 🔥 CRITICAL LOG: Verify TF switch changes data
      const rp = tfData.render_plan;
      console.log('[MTF] ═══════════════════════════════════════');
      console.log('[MTF] TF SWITCHED TO:', selectedTF);
      console.log('[MTF] Candles:', tfData.candles?.length);
      console.log('[MTF] render_plan:', !!rp);
      if (rp) {
        console.log('[MTF] > Structure swings:', rp.structure?.swings?.length);
        console.log('[MTF] > Levels:', rp.levels?.length);
        console.log('[MTF] > Market state:', rp.market_state?.trend);
        console.log('[MTF] > Execution:', rp.execution?.status);
      }
      console.log('[MTF] ═══════════════════════════════════════');
    } else if (Object.keys(tfMap).length === 0) {
      // No data at all — need initial fetch
      console.log('[MTF] No cached data, will fetch on mount');
    } else {
      // Data for some TFs exists but not for selected one
      console.log('[MTF] TF not in cache:', selectedTF, 'available:', Object.keys(tfMap));
    }
  }, [selectedTF, tfMap]);

  // Initial load
  useEffect(() => {
    fetchSetup();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol]); // Only re-fetch when symbol changes

  // Handle symbol change
  const handleSymbolSelect = (s) => {
    setSymbol(s);
    setSearchQuery('');
    setShowDropdown(false);
  };

  // Handle search - filter and show first 5
  const filteredSymbols = searchQuery
    ? SYMBOLS.filter(s => 
        s.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.replace('USDT', '').toLowerCase().includes(searchQuery.toLowerCase())
      ).slice(0, 5)
    : SYMBOLS.slice(0, 5);

  // Toggle element visibility
  const handleToggleElement = (elementKey) => {
    setActiveElements(prev => ({
      ...prev,
      [elementKey]: !prev[elementKey]
    }));
  };

  // Save idea
  const handleSaveIdea = async () => {
    try {
      setLoading(true);
      const result = await setupService.createIdea(symbol, timeframe);
      
      if (result.ok) {
        setToast(`Idea saved: ${result.idea.idea_id}`);
        setTimeout(() => setToast(null), 3000);
      }
    } catch (err) {
      setError('Failed to save idea');
    } finally {
      setLoading(false);
    }
  };

  // Share (placeholder)
  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: `${symbol} Technical Analysis`,
        text: `${setupData?.technical_bias?.toUpperCase()} bias with ${Math.round((setupData?.bias_confidence || 0) * 100)}% confidence`,
        url: window.location.href,
      });
    }
  };

  // Derived data - Map backend v2 format to component format
  // v2 returns: { primary_pattern, alternative_patterns, decision, scenarios, confidence_explanation, ... }
  
  // ═══════════════════════════════════════════════════════════════
  // PATTERN SOURCE PRIORITY (NEW GEOMETRY LAYER INTEGRATION)
  // ═══════════════════════════════════════════════════════════════
  // 1. final_analysis.ui.main_overlay (new geometry layer)
  // 2. pattern_render_contract (legacy V2 pipeline)
  // 3. primary_pattern (fallback)
  
  const finalAnalysis = setupData?.final_analysis;
  const mainOverlay = finalAnalysis?.ui?.main_overlay;
  const analysisMode = finalAnalysis?.analysis_mode;
  
  // Get pattern based on activePatternId
  // PRIORITY: Use final_analysis.ui.main_overlay if figure mode
  const renderContract = mainOverlay?.geometry ? {
    // Convert new geometry format to legacy render contract format
    type: mainOverlay.type,
    render_mode: mainOverlay.render_mode,
    geometry_contract: mainOverlay.geometry,
    boundaries: mainOverlay.geometry?.boundaries ? [
      { id: 'upper', ...mainOverlay.geometry.boundaries.upper },
      { id: 'lower', ...mainOverlay.geometry.boundaries.lower },
    ] : [],
    window: mainOverlay.geometry?.window,
    anchors: mainOverlay.geometry?.anchors,
    confidence: mainOverlay.geometry?.shape_metrics?.cleanliness || 0.6,
  } : setupData?.pattern_render_contract;
  
  const legacyPrimaryPattern = setupData?.primary_pattern;
  
  // V2: Get pattern from render_plan.patterns.primary (with forward extension for ranges)
  const renderPlanPattern = setupData?.render_plan?.patterns?.primary;
  
  // Build unified pattern object from render contract
  const primaryPattern = React.useMemo(() => {
    // PRIORITY 1: Use render_plan.patterns.primary (has correct points with forward extension)
    if (renderPlanPattern?.points) {
      console.log('[ResearchViewNew] Using render_plan pattern with points:', renderPlanPattern.type);
      return {
        ...(legacyPrimaryPattern || {}),
        ...(renderContract || {}),
        // Use render_plan pattern data (has correct forward extension)
        type: renderPlanPattern.type,
        is_active: renderPlanPattern.is_active,
        points: renderPlanPattern.points,  // CRITICAL: upper/lower/mid with forward extension
        forward_bars: renderPlanPattern.forward_bars,
        confidence: renderPlanPattern.confidence || renderPlanPattern.score,
        direction: renderPlanPattern.bias,
        breakout_level: renderPlanPattern.breakout_level,
        invalidation: renderPlanPattern.invalidation_level,
      };
    }
    
    // PRIORITY 2: Use anchor-based render contract
    if (renderContract) {
      // Use anchor-based pattern data - OVERRIDE legacy values
      return {
        // Legacy data as fallback
        ...(legacyPrimaryPattern || {}),
        // OVERRIDE with render contract values (anchor-based)
        type: renderContract.type,
        direction: renderContract.direction,
        final_score: renderContract.confidence,
        touch_score: renderContract.touch_score,
        render_quality: renderContract.render_quality,
        breakout_level: renderContract.render?.levels?.[0]?.price,
        invalidation: null,
        anchor_points: renderContract.anchors,
      };
    }
    return legacyPrimaryPattern;
  }, [renderContract, legacyPrimaryPattern, renderPlanPattern]);
  
  const alternativePatterns = setupData?.alternative_patterns || [];
  
  // Determine which pattern to display on chart
  const getActivePattern = () => {
    if (activePatternId === 'primary') return primaryPattern;
    const altIndex = parseInt(activePatternId.replace('alt-', ''));
    return alternativePatterns[altIndex] || primaryPattern;
  };
  
  const pattern = getActivePattern();
  
  // LEVELS — use from render_plan (max 5, ranked by strength)
  const levels = React.useMemo(() => {
    const rpLevels = setupData?.render_plan?.levels;
    if (rpLevels?.length) {
      // Convert to format ResearchChart expects
      return rpLevels.map(l => ({
        price: l.price,
        type: l.type, // support/resistance
        strength: l.strength,
        source: l.source,
      }));
    }
    return setupData?.levels || [];
  }, [setupData?.render_plan?.levels, setupData?.levels]);
  
  const structure = setupData?.structure;
  const setup = setupData?.setup;
  
  // New v2 data
  const decision = setupData?.decision;
  
  // BUILD scenarios from decision and structure
  const scenarios = React.useMemo(() => {
    if (!setupData) return [];
    
    const decisionData = setupData.decision;
    const structure = setupData.structure_context;
    const pattern = setupData.primary_pattern;
    const rp = setupData.render_plan;
    const currentPrice = setupData.current_price || rp?.market_state?.current_price;
    const levels = rp?.levels || [];
    
    const result = [];
    
    // Bullish scenario
    const resistances = levels.filter(l => l.type === 'resistance' && l.price > currentPrice);
    const nearestResistance = resistances.length > 0 ? resistances.reduce((a, b) => b.price < a.price ? b : a) : null;
    
    if (nearestResistance) {
      result.push({
        id: 'bullish',
        type: 'bullish',
        title: 'Bullish Breakout',
        description: `Break above ${nearestResistance.price?.toFixed(0)} triggers bullish continuation`,
        probability: decisionData?.bias === 'bullish' ? 0.6 : decisionData?.bias === 'neutral' ? 0.4 : 0.3,
        trigger_price: nearestResistance.price,
        target_price: nearestResistance.price * 1.03,
      });
    }
    
    // Bearish scenario
    const supports = levels.filter(l => l.type === 'support' && l.price < currentPrice);
    const nearestSupport = supports.length > 0 ? supports.reduce((a, b) => b.price > a.price ? b : a) : null;
    
    if (nearestSupport) {
      result.push({
        id: 'bearish',
        type: 'bearish',
        title: 'Bearish Breakdown',
        description: `Break below ${nearestSupport.price?.toFixed(0)} triggers bearish move`,
        probability: decisionData?.bias === 'bearish' ? 0.6 : decisionData?.bias === 'neutral' ? 0.4 : 0.3,
        trigger_price: nearestSupport.price,
        target_price: nearestSupport.price * 0.97,
      });
    }
    
    // Range scenario (if both levels exist)
    if (nearestResistance && nearestSupport) {
      result.push({
        id: 'range',
        type: 'neutral',
        title: 'Range Continuation',
        description: `Price consolidates between ${nearestSupport.price?.toFixed(0)} - ${nearestResistance.price?.toFixed(0)}`,
        probability: decisionData?.bias === 'neutral' ? 0.5 : 0.3,
        trigger_price: currentPrice,
        target_price: null,
      });
    }
    
    return result;
  }, [setupData]);
  
  // BUILD confidenceExplanation from decision - format for ConfidenceExplanation component
  const confidenceExplanation = React.useMemo(() => {
    if (!setupData?.decision) return {};
    
    const d = setupData.decision;
    const pattern = setupData.primary_pattern;
    
    // If we have pattern scores, use them
    if (pattern?.scores) {
      const scores = pattern.scores;
      return {
        geometry: scores.geometry || 0.5,
        structure: scores.structure || 0.5,
        level: scores.level || 0.5,
        recency: scores.recency || 0.5,
        cleanliness: scores.cleanliness || 0.5,
      };
    }
    
    // Otherwise build from decision data
    // Convert string bias to numeric score
    const biasToScore = (bias) => {
      if (bias === 'bullish' || bias === 'bearish') return 0.8;
      if (bias === 'lean_bullish' || bias === 'lean_bearish') return 0.6;
      return 0.5;
    };
    
    const strengthToScore = (strength) => {
      if (strength === 'high' || strength === 'strong') return 0.85;
      if (strength === 'medium' || strength === 'moderate') return 0.65;
      return 0.45;
    };
    
    return {
      structure: biasToScore(d.indicator_bias),
      level: strengthToScore(d.strength),
      geometry: d.confidence || 0.5,
      recency: d.alignment === 'aligned' ? 0.8 : d.alignment === 'mixed' ? 0.5 : 0.4,
      cleanliness: d.tradeability === 'high' ? 0.8 : d.tradeability === 'medium' ? 0.6 : 0.4,
    };
  }, [setupData]);
  
  // BUILD explanation from decision and pattern — format for ExplanationPanel
  const explanation = React.useMemo(() => {
    if (!setupData) return null;
    
    const d = setupData.decision;
    const pattern = setupData.primary_pattern;
    const levels = setupData.render_plan?.levels || [];
    const currentPrice = setupData.current_price;
    
    if (!d && !pattern) return null;
    
    // Build summary
    let summary = '';
    if (d?.summary) {
      summary = d.summary;
    } else if (pattern?.type) {
      summary = `${pattern.type.replace(/_/g, ' ')} pattern detected with ${pattern.direction || 'neutral'} bias.`;
    } else {
      summary = 'Market conditions being analyzed.';
    }
    
    // Build action
    let action = '';
    if (d?.bias === 'bullish' && d?.tradeability === 'high') {
      action = 'Look for long entries on pullbacks to support.';
    } else if (d?.bias === 'bearish' && d?.tradeability === 'high') {
      action = 'Look for short entries on rallies to resistance.';
    } else if (d?.tradeability === 'medium') {
      action = 'Wait for clearer setup before taking position.';
    } else {
      action = 'No clear action — observe and wait for better conditions.';
    }
    
    // Build risk
    let risk = '';
    const resistances = levels.filter(l => l.type === 'resistance' && l.price > currentPrice);
    const supports = levels.filter(l => l.type === 'support' && l.price < currentPrice);
    
    if (d?.bias === 'bullish' && supports.length > 0) {
      const nearestSupport = supports.reduce((a, b) => b.price > a.price ? b : a);
      risk = `Invalidation below ${nearestSupport.price?.toFixed(0)} support level.`;
    } else if (d?.bias === 'bearish' && resistances.length > 0) {
      const nearestResistance = resistances.reduce((a, b) => b.price < a.price ? b : a);
      risk = `Invalidation above ${nearestResistance.price?.toFixed(0)} resistance level.`;
    } else {
      risk = 'Define clear stop-loss before entering any position.';
    }
    
    // Confidence
    let confidence = 'medium';
    if (d?.confidence >= 0.7 || d?.tradeability === 'high') confidence = 'high';
    else if (d?.confidence <= 0.3 || d?.tradeability === 'low') confidence = 'low';
    
    return { summary, action, risk, confidence };
  }, [setupData]);
  
  // TRADE SETUP — Execution-ready entry/stop/targets
  const tradeSetup = setupData?.trade_setup || null;
  
  // BASE LAYER — always visible
  const baseLayer = setupData?.base_layer || null;
  
  // Structure context from V2 engine (rich data)
  const structureContext = setupData?.structure_context || null;
  
  // STRUCTURE VISUALIZATION — pivot points, BOS/CHOCH, trendlines
  const structureVisualization = setupData?.structure_visualization || null;
  
  // CHART STRUCTURE — build from render_plan.structure for chart rendering
  // Format: { labels: [{time, price, label, type}], breaks: [...], legs: [...] }
  const chartStructure = React.useMemo(() => {
    const rpStructure = setupData?.render_plan?.structure;
    if (!rpStructure?.swings?.length) return null;
    
    // Convert swings to labels format that ResearchChart expects
    const labels = rpStructure.swings.map(s => ({
      time: s.time,
      price: s.price,
      label: s.type, // HH/HL/LH/LL
      type: s.type?.includes('H') && s.type !== 'HL' ? 'high' : 'low',
    }));
    
    // Build breaks from BOS/CHOCH
    const breaks = [];
    if (rpStructure.bos) {
      breaks.push({
        time: rpStructure.bos.time,
        level: rpStructure.bos.price,
        type: 'bos',
        direction: rpStructure.bos.direction,
      });
    }
    if (rpStructure.choch) {
      breaks.push({
        time: rpStructure.choch.time,
        level: rpStructure.choch.price,
        type: 'choch',
        direction: rpStructure.choch.direction,
      });
    }
    
    return { labels, breaks, legs: [] };
  }, [setupData?.render_plan?.structure]);
  
  // TA CONTEXT — unified contributions from all TA sources
  // Transform backend format to TAContextPanel expected format
  const taContext = React.useMemo(() => {
    const rawContext = setupData?.ta_context;
    if (!rawContext) return null;
    
    const indicators = rawContext.indicators || {};
    const signals = indicators.signals || [];
    
    // Count bullish/bearish/neutral from signals
    let bullishCount = 0;
    let bearishCount = 0;
    let neutralCount = 0;
    let bullishScore = 0;
    let bearishScore = 0;
    
    const bullishSignals = [];
    const bearishSignals = [];
    const neutralSignals = [];
    
    signals.forEach(s => {
      const direction = s.direction?.toLowerCase();
      const strength = s.strength || 0;
      const item = {
        name: s.name,
        signal_type: s.signal_type,
        strength: strength,
        description: s.description,
        signal: direction,
        score: direction === 'bullish' ? strength : direction === 'bearish' ? -strength : 0,
        source: 'indicator',
        impact: strength / (signals.length || 1),
      };
      
      if (direction === 'bullish') {
        bullishCount++;
        bullishScore += strength;
        bullishSignals.push(item);
      } else if (direction === 'bearish') {
        bearishCount++;
        bearishScore += strength;
        bearishSignals.push(item);
      } else {
        neutralCount++;
        neutralSignals.push(item);
      }
    });
    
    // Calculate aggregated bias and score
    const totalScore = bullishScore - bearishScore;
    const maxPossibleScore = signals.length * 1; // max strength is 1
    const normalizedScore = maxPossibleScore > 0 ? totalScore / maxPossibleScore : 0;
    
    let aggregatedBias = 'neutral';
    if (normalizedScore > 0.1) aggregatedBias = 'bullish';
    else if (normalizedScore < -0.1) aggregatedBias = 'bearish';
    
    // Sort by strength for top_drivers
    const allContribs = [...bullishSignals, ...bearishSignals, ...neutralSignals]
      .sort((a, b) => Math.abs(b.strength) - Math.abs(a.strength));
    
    return {
      summary: {
        aggregated_bias: aggregatedBias,
        aggregated_score: normalizedScore,
        aggregated_confidence: Math.min(1, (bullishCount + bearishCount) / (signals.length || 1)),
        total_sources: signals.length,
        active_sources: bullishCount + bearishCount,
      },
      indicators: {
        bullish: bullishCount,
        bearish: bearishCount,
        neutral: neutralCount,
        total: signals.length,
      },
      top_drivers: allContribs.slice(0, 10),
      all_contributions: allContribs,
      hidden_but_used: [],
      rendered_default: [],
    };
  }, [setupData?.ta_context]);
  
  // RENDER PLAN — brain → chart mapping (from VisualMappingEngine)
  const renderPlan = setupData?.render_plan || null;
  
  // ════════════════════════════════════════════════════════════════
  // CONFLUENCE ENGINE — TA Decision Logic (NEW!)
  // Transforms raw data into actionable analysis
  // ════════════════════════════════════════════════════════════════
  const confluence = React.useMemo(() => {
    const result = buildConfluence(renderPlan);
    if (result) {
      console.log('[CONFLUENCE] ═══════════════════════════════════');
      console.log('[CONFLUENCE] TF:', selectedTF);
      console.log('[CONFLUENCE] Bias:', result.bias, '| Strength:', result.strength);
      console.log('[CONFLUENCE] Score:', result.score);
      console.log('[CONFLUENCE] Decision:', result.decision);
      console.log('[CONFLUENCE] Signals:', result.signals);
      console.log('[CONFLUENCE] ═══════════════════════════════════');
    }
    return result;
  }, [renderPlan, selectedTF]);
  
  // TRADE SETUP — generated from confluence analysis
  const generatedTradeSetup = React.useMemo(() => {
    return buildTradeSetup(renderPlan, confluence);
  }, [renderPlan, confluence]);
  
  // MODE-BASED LAYER VISIBILITY — Auto/Classic/Smart/Minimal
  const modeLayerVisibility = React.useMemo(() => {
    return getLayerVisibility(viewMode);
  }, [viewMode]);
  
  // TA COMPOSITION — complete technical setup view (BUILD FROM DATA!)
  const taComposition = React.useMemo(() => {
    if (!setupData) return null;
    
    const pattern = setupData.primary_pattern;
    const fib = setupData.fib;
    const rp = setupData.render_plan;
    const indicators = setupData.indicators;
    const decision = setupData.decision;
    
    // Если нет паттерна и нет данных — нет setup
    const hasPattern = pattern && pattern.type;
    const hasFib = fib && fib.levels?.length > 0;
    
    // Build active_figure from primary_pattern
    let active_figure = null;
    if (hasPattern) {
      active_figure = {
        type: pattern.type,
        direction: pattern.direction,
        confidence: pattern.confidence || 0.5,
        breakout_level: pattern.breakout_price || pattern.upper_line?.end_price,
        invalidation_level: pattern.invalidation_price || pattern.lower_line?.end_price,
      };
    }
    
    // Build active_fib from fib data
    let active_fib = null;
    if (hasFib) {
      const fibLevels = fib.levels || [];
      active_fib = {
        swing_type: fib.type || 'retracement',
        current_position: fib.current_zone || 'between_levels',
        key_levels: fibLevels.slice(0, 5).map(l => ({
          level: l.level,
          price: l.price,
          status: l.status || 'active',
        })),
      };
    }
    
    // Build relevant_overlays from indicators
    const relevant_overlays = [];
    if (indicators?.overlays) {
      indicators.overlays.slice(0, 3).forEach(o => {
        const lastValue = o.data?.[o.data.length - 1]?.value;
        if (lastValue) {
          relevant_overlays.push({
            display_name: o.name || o.id,
            current_value: lastValue,
          });
        }
      });
    }
    
    // Build breakout_logic from pattern or levels
    let breakout_logic = null;
    const levels = rp?.levels || setupData.levels || [];
    const currentPrice = setupData.current_price || rp?.market_state?.current_price;
    
    if (levels.length > 0 && currentPrice) {
      const resistances = levels.filter(l => l.type === 'resistance' && l.price > currentPrice);
      const supports = levels.filter(l => l.type === 'support' && l.price < currentPrice);
      
      const nearestResistance = resistances.length > 0 ? resistances.reduce((a, b) => b.price < a.price ? b : a) : null;
      const nearestSupport = supports.length > 0 ? supports.reduce((a, b) => b.price > a.price ? b : a) : null;
      
      if (nearestResistance || nearestSupport) {
        breakout_logic = {
          breakout_level: nearestResistance?.price,
          invalidation_level: nearestSupport?.price,
          breakout_type: 'resistance_break',
          risk_pct: currentPrice && nearestSupport ? ((currentPrice - nearestSupport.price) / currentPrice * 100) : null,
        };
      }
    }
    
    // Determine setup quality
    let setup_quality = 'low';
    if (hasPattern && pattern.confidence > 0.7) setup_quality = 'high';
    else if (hasPattern && pattern.confidence > 0.5) setup_quality = 'medium';
    else if (hasFib || levels.length > 0) setup_quality = 'medium';
    
    // Build setup_summary with lifecycle info
    let setup_summary = '';
    
    // Check for display_message from Display Gate (pattern rejected)
    const displayMessage = setupData?.display_message;
    
    if (displayMessage && !hasPattern) {
      // Display Gate rejected pattern - show fallback message
      setup_summary = displayMessage;
    } else if (hasPattern) {
      const lifecycle = pattern.lifecycle;
      const lifecycleStage = lifecycle?.stage || 'forming';
      const completion = lifecycle?.completion || 0;
      
      // Add lifecycle stage badge
      const stageBadges = {
        'forming': '🔄 Forming',
        'maturing': '⏳ Maturing',
        'confirmed': '✅ Confirmed',
        'broken': '❌ Broken',
        'invalidated': '⚠️ Invalidated',
      };
      const stageBadge = stageBadges[lifecycleStage] || lifecycleStage;
      
      setup_summary = `${pattern.label || pattern.type?.replace(/_/g, ' ')} — ${stageBadge}`;
      
      // Add completion percentage for forming/maturing
      if (lifecycleStage === 'forming' || lifecycleStage === 'maturing') {
        setup_summary += ` (${Math.round(completion * 100)}%)`;
      }
      
      // Add direction bias
      if (pattern.direction) {
        setup_summary += ` · ${pattern.direction.charAt(0).toUpperCase() + pattern.direction.slice(1)} bias`;
      }
      
      // Add state reason if available
      if (lifecycle?.state_reason) {
        setup_summary = lifecycle.state_reason;
      }
    } else if (decision?.summary) {
      setup_summary = decision.summary;
    } else {
      setup_summary = 'Analyzing market structure...';
    }
    
    return {
      has_active_setup: hasPattern || hasFib || levels.length > 0,
      setup_quality,
      setup_summary,
      active_figure,
      active_fib,
      relevant_overlays,
      breakout_logic,
      active_zone: null,
      structure_context: decision?.context || 'neutral',
    };
  }, [setupData]);
  
  // ═══════════════════════════════════════════════════════════════
  // MARKET MECHANICS — POI, Liquidity from render_plan
  // ═══════════════════════════════════════════════════════════════
  const poi = setupData?.poi || null;
  
  // LIQUIDITY — prioritize render_plan over raw data
  const liquidity = React.useMemo(() => {
    const rpLiquidity = setupData?.render_plan?.liquidity;
    if (rpLiquidity) {
      // Convert render_plan format to MarketMechanicsRenderer format
      const pools = [];
      
      // Add BSL (above price)
      (rpLiquidity.bsl || []).forEach(bsl => {
        const price = typeof bsl.price === 'number' ? bsl.price : parseFloat(bsl.price);
        pools.push({
          type: 'buy_side_liquidity',
          side: 'high',
          price: price,
          strength: bsl.strength,
          touches: bsl.touches,
          label: bsl.label || `BSL @ ${price ? Math.round(price) : 'N/A'}`,
          status: 'active',
        });
      });
      
      // Add SSL (below price)
      (rpLiquidity.ssl || []).forEach(ssl => {
        const price = typeof ssl.price === 'number' ? ssl.price : parseFloat(ssl.price);
        pools.push({
          type: 'sell_side_liquidity',
          side: 'low',
          price: price,
          strength: ssl.strength,
          touches: ssl.touches,
          label: ssl.label || `SSL @ ${price ? Math.round(price) : 'N/A'}`,
          status: 'active',
        });
      });
      
      return {
        pools,
        sweeps: rpLiquidity.sweeps || [],
        equal_highs: [],
        equal_lows: [],
      };
    }
    return setupData?.liquidity || null;
  }, [setupData?.render_plan?.liquidity, setupData?.liquidity]);
  
  const chochValidation = setupData?.choch_validation || null;
  const displacement = setupData?.displacement || null;
  
  // ═══════════════════════════════════════════════════════════════
  // EXECUTION — prioritize render_plan execution (always visible!)
  // ═══════════════════════════════════════════════════════════════
  const execution = React.useMemo(() => {
    const rpExecution = setupData?.render_plan?.execution;
    if (rpExecution) {
      return rpExecution;
    }
    return setupData?.execution || null;
  }, [setupData?.render_plan?.execution, setupData?.execution]);
  
  const chainMap = setupData?.chain_map || [];
  const unifiedSetupData = setupData?.unified_setup || null;
  const fib = setupData?.fib || null;
  
  // Handle pattern click (switch between primary/alternatives)
  const handlePatternClick = (patternId) => {
    setActivePatternId(patternId);
  };
  
  // Handle scenario click (highlight corresponding pattern)
  const handleScenarioClick = (scenario) => {
    // Map scenario to pattern
    if (scenario.pattern) {
      const altIndex = alternativePatterns.findIndex(p => p.type === scenario.pattern);
      if (altIndex >= 0) {
        setActivePatternId(`alt-${altIndex}`);
      } else if (primaryPattern?.type === scenario.pattern) {
        setActivePatternId('primary');
      }
    }
  };
  
  // Map structure to array format for PatternActivationLayer
  const structureArray = structure ? [
    ...Array(structure.hh || 0).fill({ type: 'HH' }),
    ...Array(structure.hl || 0).fill({ type: 'HL' }),
    ...Array(structure.lh || 0).fill({ type: 'LH' }),
    ...Array(structure.ll || 0).fill({ type: 'LL' }),
  ] : [];
  
  // Build unified setup object for all components
  const unifiedSetup = React.useMemo(() => {
    if (!setupData) return null;
    
    const d = setupData.decision;
    const rp = setupData.render_plan;
    const indicators = setupData.indicator_result || setupData.ta_context?.indicators?.signals || [];
    const structureState = setupData.structure_state || setupData.structure_context;
    
    // Build structure array from structure_state swings or render_plan structure
    const buildStructureArray = () => {
      const swings = rp?.structure?.swings || [];
      if (swings.length > 0) {
        return swings.map(s => ({ type: s.type, time: s.time, price: s.price }));
      }
      // Fallback to structure_state counts
      if (structureState) {
        const arr = [];
        for (let i = 0; i < (structureState.hh_count || 0); i++) arr.push({ type: 'HH' });
        for (let i = 0; i < (structureState.hl_count || 0); i++) arr.push({ type: 'HL' });
        for (let i = 0; i < (structureState.lh_count || 0); i++) arr.push({ type: 'LH' });
        for (let i = 0; i < (structureState.ll_count || 0); i++) arr.push({ type: 'LL' });
        return arr;
      }
      return structureArray;
    };
    
    // Build indicators array from indicator_result
    const buildIndicatorsArray = () => {
      if (Array.isArray(indicators) && indicators.length > 0) {
        return indicators.map(ind => ({
          name: ind.name,
          direction: ind.direction?.toLowerCase(),
          signal_type: ind.signal_type,
          strength: ind.strength,
          description: ind.description,
        }));
      }
      return [];
    };
    
    // Derive bias and confidence from decision
    const derivedBias = d?.bias || (pattern?.direction) || 'neutral';
    const derivedConfidence = d?.confidence || pattern?.confidence || 0;
    const derivedSetupType = pattern?.type || (rp?.market_state?.trend_direction) || 'analysis';
    
    return {
      // Pattern as array (for PatternActivationLayer)
      patterns: pattern ? [{
        type: pattern.type,
        confidence: pattern.confidence,
        direction: pattern.direction || derivedBias,
        points: pattern.points,
      }] : [],
      
      // Single pattern object (for ResearchChart)
      pattern: pattern,
      
      // Levels array - from render_plan or computed levels
      levels: levels,
      
      // Structure as array with actual data
      structure: buildStructureArray(),
      
      // Setup details from decision
      setup_type: derivedSetupType,
      direction: derivedBias,
      confidence: derivedConfidence,
      confluence_score: d?.confidence || 0,
      trigger: setup?.trigger,
      invalidation: setup?.invalidation,
      targets: setup?.targets || [],
      
      // Indicators from API
      indicators: buildIndicatorsArray(),
      
      // Conflicts/risks
      conflicts: [],
      
      // Market context from decision and render_plan
      market_regime: rp?.market_state?.trend_direction || structureState?.regime || d?.context || 'neutral',
      asset: symbol,
      timeframe: selectedTF,
      current_price: setupData.current_price,
      
      // Additional fields for DeepAnalysisBlocks
      primary_confluence: d ? {
        score: d.confidence,
        components: [d.bias, d.strength].filter(Boolean),
      } : null,
      explanation: d?.summary,
    };
  }, [setupData, pattern, levels, structureArray, setup, symbol, selectedTF]);
  
  const technicalBias = unifiedSetup?.direction || 'neutral';
  const biasConfidence = unifiedSetup?.confidence || 0;

  // ═══════════════════════════════════════════════════════════════
  // GRAPH VISIBILITY ENGINE — Intelligent layer prioritization
  // ═══════════════════════════════════════════════════════════════
  const currentPrice = candles?.length > 0 ? candles[candles.length - 1]?.close : null;
  
  // Get pattern from render_plan.patterns.primary (v2) OR legacy primary_pattern
  const rpPatternPrimary = setupData?.render_plan?.patterns?.primary;
  const effectivePattern = rpPatternPrimary || setupData?.primary_pattern;
  
  const visibilityContext = {
    setup: setupData?.setup,
    pattern_primary: effectivePattern,  // Use v2 pattern from render_plan
    pattern_alternative: setupData?.alternative_patterns?.[0],
    poi: poi,
    liquidity: liquidity,
    fib: setupData?.fibonacci,
    indicators: setupData?.indicators,
    choch: chochValidation,
    displacement: displacement,
    structure_context: structureContext || structure,
    current_price: currentPrice,
  };
  
  const layerVisibilityComputed = computeVisibility(visibilityContext, viewMode, renderPlan);
  console.log('[Visibility] viewMode:', viewMode, 'renderPlan:', renderPlan);
  console.log('[Visibility] computed:', layerVisibilityComputed);
  console.log('[Visibility] context keys with data:', Object.keys(visibilityContext).filter(k => visibilityContext[k]));
  const limits = getLayerLimits(viewMode);
  
  // Apply limits to data with price-based prioritization
  const limitedPOI = poi ? {
    ...poi,
    zones: applyLimits(poi.zones, 'poi_zones', limits, currentPrice),
  } : null;
  
  const limitedLiquidity = liquidity ? {
    ...liquidity,
    equal_highs: applyLimits(liquidity.equal_highs, 'liquidity_levels', limits, currentPrice),
    equal_lows: applyLimits(liquidity.equal_lows, 'liquidity_levels', limits, currentPrice),
  } : null;

  // Get visual styles for layers
  const poiStyle = getLayerStyle('poi');
  const liquidityStyle = getLayerStyle('liquidity');
  const patternStyle = getLayerStyle('pattern_primary');
  const fibStyle = getLayerStyle('fib');

  // ═══════════════════════════════════════════════════════════════
  // PATTERN VIEW MODE — isolates pattern for readability
  // When active: hide structure, levels, indicators, liquidity
  // Keep: candles + active pattern + breakout/neckline
  // ═══════════════════════════════════════════════════════════════
  
  // Determine what to show based on view mode
  // PATTERN VIEW MODE overrides normal visibility settings
  const showPatterns = viewMode !== 'clean' && layerVisibilityComputed.patterns;
  const showLevels = patternViewMode ? false : (layerVisibilityComputed.levels !== false);
  const showStructure = patternViewMode ? false : layerVisibilityComputed.structure;
  const showIndicators = patternViewMode ? false : (viewMode === 'manual');
  const showBaseLayer = patternViewMode ? true : (viewMode !== 'minimal');
  
  // Additional visibility controls for Pattern View mode
  const showMarketMechanicsComputed = patternViewMode ? false : (viewMode !== 'classic');
  const showLiquidityComputed = patternViewMode ? false : layerVisibilityComputed.liquidity;
  const showPOIComputed = patternViewMode ? false : layerVisibilityComputed.poi;
  const showSweepsComputed = patternViewMode ? false : layerVisibilityComputed.liquidity;
  const showCHOCHComputed = patternViewMode ? false : layerVisibilityComputed.structure;

  return (
    <Container data-testid="research-view">
      {/* Top Control Bar */}
      <TopBar>
        <ControlsLeft>
          {/* Search Asset */}
          <SearchWrapper>
            <SearchInput
              type="text"
              placeholder="Search"
              value={showDropdown ? searchQuery : (searchQuery || '')}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setShowDropdown(true);
              }}
              onFocus={() => setShowDropdown(true)}
              onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
              data-testid="asset-search"
            />
            {showDropdown && filteredSymbols.length > 0 && (
              <SymbolDropdown>
                {filteredSymbols.map(s => (
                  <SymbolOption
                    key={s}
                    $active={s === symbol}
                    onMouseDown={() => handleSymbolSelect(s)}
                  >
                    {s.replace('USDT', '')}
                  </SymbolOption>
                ))}
              </SymbolDropdown>
            )}
          </SearchWrapper>

          {/* MTF Timeframe Selector — ALL TIMEFRAMES */}
          <TfGroup>
            {TIMEFRAMES.map(tf => (
              <TfButton
                key={tf}
                $active={selectedTF === tf}
                onClick={() => setSelectedTF(tf)}
                data-testid={`tf-${tf}`}
              >
                {TF_DISPLAY_NAMES[tf] || tf}
              </TfButton>
            ))}
          </TfGroup>

          {/* Chart Type */}
          <ChartTypeGroup>
            <ChartTypeBtn
              $active={chartType === 'candles'}
              onClick={() => setChartType('candles')}
              title="Candles"
            >
              <BarChart2 />
            </ChartTypeBtn>
            <ChartTypeBtn
              $active={chartType === 'line'}
              onClick={() => setChartType('line')}
              title="Line"
            >
              <LineChart />
            </ChartTypeBtn>
          </ChartTypeGroup>

          {/* Layer Toggles removed - using ViewModeSelector below chart instead */}
        </ControlsLeft>
      </TopBar>

      {/* ════════════════════════════════════════════════════════════════ */}
      {/* CHART CONTROLS — View mode, Indicators, Overlays (moved above chart) */}
      {/* ════════════════════════════════════════════════════════════════ */}
      {!loading && (
        <SubChartControls data-testid="sub-chart-controls">
          {/* View Mode Section */}
          <span className="section-label">View</span>
          <ViewModeSelector
            mode={viewMode}
            onChange={setViewMode}
          />
          
          <ControlDivider />
          
          {/* Indicators Section */}
          <span className="section-label">Indicators</span>
          <IndicatorSelector
            selectedOverlays={selectedOverlays}
            selectedPanes={selectedPanes}
            onOverlaysChange={setSelectedOverlays}
            onPanesChange={setSelectedPanes}
          />
          
          <ControlDivider />
          
          {/* Chart Overlays Section - OFF by default */}
          <span className="section-label">Overlays</span>
          <div className="overlay-section">
            <CollapsibleButton
              $active={showFibonacciOverlay}
              onClick={() => setShowFibonacciOverlay(!showFibonacciOverlay)}
              data-testid="fibonacci-toggle-btn"
              title="Show Fibonacci retracement levels on chart"
            >
              <RefreshCw size={13} />
              Fib
            </CollapsibleButton>
            <CollapsibleButton
              $active={showPatternOverlay}
              onClick={() => setShowPatternOverlay(!showPatternOverlay)}
              data-testid="pattern-toggle-btn"
              title="Show detected pattern info card on chart"
            >
              <Triangle size={13} />
              Pattern
            </CollapsibleButton>
            
            {/* PATTERN VIEW MODE — Isolates pattern for readability */}
            {/* CRITICAL: Only show if analysis_mode === "figure" */}
            {showPatternOverlay && analysisMode === 'figure' && renderContract && (
              <button
                data-testid="pattern-view-btn"
                onClick={() => setPatternViewMode(!patternViewMode)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '4px 8px',
                  background: patternViewMode ? '#3b82f6' : '#1e293b',
                  border: `1px solid ${patternViewMode ? '#3b82f6' : '#334155'}`,
                  borderRadius: '4px',
                  color: '#f1f5f9',
                  fontSize: '11px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
                title="Pattern View Mode — isolates pattern, hides structure/levels"
              >
                <Eye size={12} />
                {patternViewMode ? 'View ON' : 'View'}
              </button>
            )}
            
            {/* PATTERN SWITCHER — V4: Switch between primary and alternatives */}
            {showPatternOverlay && setupData?.alternative_render_contracts?.length > 0 && (
              <button
                data-testid="pattern-switcher-btn"
                onClick={() => {
                  const totalPatterns = 1 + (setupData?.alternative_render_contracts?.length || 0);
                  setPatternIndex((patternIndex + 1) % totalPatterns);
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '4px 8px',
                  background: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '4px',
                  color: '#f1f5f9',
                  fontSize: '11px',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
                title="Switch between detected patterns"
              >
                {patternIndex + 1}/{1 + (setupData?.alternative_render_contracts?.length || 0)}
              </button>
            )}
            
            <CollapsibleButton
              $active={showSetupOverlay}
              onClick={() => setShowSetupOverlay(!showSetupOverlay)}
              data-testid="setup-toggle-btn"
              title="Show trade setup info card on chart"
            >
              <Target size={13} />
              Setup
            </CollapsibleButton>
            <CollapsibleButton
              $active={showTAOverlay}
              onClick={() => setShowTAOverlay(!showTAOverlay)}
              data-testid="ta-overlay-toggle-btn"
              title="Show full TA analysis overlay on chart"
            >
              <Layers size={13} />
              TA
            </CollapsibleButton>
          </div>
        </SubChartControls>
      )}

      {/* Main Content */}
      <MainContent>
        {/* ════════════════════════════════════════════════════════════════ */}
        {/* MTF SUMMARY BAR — One-line TA summary above chart */}
        {/* ════════════════════════════════════════════════════════════════ */}
        {mtfContext?.summary?.summary_text && (
          <div 
            data-testid="mtf-summary-bar"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '10px 16px',
              background: '#0f172a',
              borderRadius: '8px',
              marginBottom: '12px',
            }}
          >
            <span style={{
              fontSize: '13px',
              fontWeight: '600',
              color: '#ffffff',
              letterSpacing: '0.3px',
            }}>
              {mtfContext.summary.summary_text}
            </span>
          </div>
        )}
        
        {/* MTF ALIGNMENT BOX — Multi-timeframe alignment (NEW!) */}
        {mtfContext?.alignment && (
          <div 
            data-testid="mtf-alignment-box"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              padding: '10px 16px',
              background: mtfContext.alignment.direction === 'bullish' 
                ? 'rgba(5, 165, 132, 0.08)' 
                : mtfContext.alignment.direction === 'bearish'
                ? 'rgba(239, 68, 68, 0.08)'
                : 'rgba(148, 163, 184, 0.08)',
              border: `1px solid ${
                mtfContext.alignment.direction === 'bullish' 
                  ? 'rgba(5, 165, 132, 0.2)' 
                  : mtfContext.alignment.direction === 'bearish'
                  ? 'rgba(239, 68, 68, 0.2)'
                  : 'rgba(148, 163, 184, 0.2)'
              }`,
              borderRadius: '8px',
              marginBottom: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{
                fontSize: '10px',
                fontWeight: '700',
                color: '#64748b',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}>
                MTF ALIGNMENT
              </span>
              <span style={{
                padding: '2px 8px',
                borderRadius: '4px',
                fontSize: '11px',
                fontWeight: '700',
                textTransform: 'uppercase',
                background: mtfContext.alignment.direction === 'bullish' 
                  ? 'rgba(5, 165, 132, 0.15)' 
                  : mtfContext.alignment.direction === 'bearish'
                  ? 'rgba(239, 68, 68, 0.15)'
                  : 'rgba(148, 163, 184, 0.15)',
                color: mtfContext.alignment.direction === 'bullish' 
                  ? '#05A584' 
                  : mtfContext.alignment.direction === 'bearish'
                  ? '#EF4444'
                  : '#64748b',
              }}>
                {mtfContext.alignment.direction}
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '11px', color: '#94a3b8' }}>Confidence:</span>
              <div style={{
                width: '60px',
                height: '6px',
                background: '#e2e8f0',
                borderRadius: '3px',
                overflow: 'hidden',
              }}>
                <div style={{
                  height: '100%',
                  width: `${Math.round((mtfContext.alignment.confidence || 0) * 100)}%`,
                  background: mtfContext.alignment.direction === 'bullish' 
                    ? '#05A584' 
                    : mtfContext.alignment.direction === 'bearish'
                    ? '#EF4444'
                    : '#94a3b8',
                  borderRadius: '3px',
                  transition: 'width 0.3s ease',
                }} />
              </div>
              <span style={{ 
                fontSize: '11px', 
                fontWeight: '600',
                color: mtfContext.alignment.direction === 'bullish' 
                  ? '#05A584' 
                  : mtfContext.alignment.direction === 'bearish'
                  ? '#EF4444'
                  : '#64748b',
              }}>
                {Math.round((mtfContext.alignment.confidence || 0) * 100)}%
              </span>
            </div>
          </div>
        )}
        
        {/* Per-TF Interpretation Panel — shows interpretation for selected TF */}
        {setupData?.interpretation && (
          <div 
            data-testid="tf-interpretation"
            style={{
              padding: '12px 16px',
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              marginBottom: '12px',
            }}
          >
            <div style={{
              fontSize: '10px',
              fontWeight: '700',
              color: '#64748b',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginBottom: '6px',
            }}>
              {TF_DISPLAY_NAMES[selectedTF] || selectedTF} ANALYSIS
            </div>
            <div style={{
              fontSize: '13px',
              color: '#0f172a',
              lineHeight: '1.5',
            }}>
              {setupData.interpretation}
            </div>
          </div>
        )}
        
        {/* NARRATIVE BOX — Market Story (NEW!) */}
        {setupData?.narrative?.full && (
          <div 
            data-testid="narrative-box"
            style={{
              padding: '12px 16px',
              background: 'rgba(15, 23, 42, 0.03)',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              marginBottom: '12px',
            }}
          >
            <div style={{
              fontSize: '10px',
              fontWeight: '700',
              color: '#94a3b8',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginBottom: '6px',
            }}>
              MARKET NARRATIVE
            </div>
            <div style={{
              fontSize: '13px',
              color: '#475569',
              lineHeight: '1.6',
              fontStyle: 'italic',
            }}>
              {setupData.narrative.full}
            </div>
          </div>
        )}
        
        {/* Error Banner */}
        {error && (
          <ErrorBanner>
            <AlertTriangle size={18} />
            {error}
          </ErrorBanner>
        )}

        {/* ════════════════════════════════════════════════════════════════ */}
        {/* CHART FIRST — Main focus at the top */}
        {/* ════════════════════════════════════════════════════════════════ */}
        <ChartSection style={{ position: 'relative' }}>
          <ResearchChart
            candles={candles}
            // PRIMARY DATA SOURCE: render_plan from backend
            renderPlan={renderPlan}
            // V4 RENDER CONTRACT — pattern_render_contract for clean TA formations
            // CRITICAL: Pass ta_layers and active_range for proper overlay rendering
            data={{
              pattern_render_contract: patternV2?.renderContract || (patternIndex === 0 
                ? setupData?.pattern_render_contract 
                : setupData?.alternative_render_contracts?.[patternIndex - 1]),
              alternative_render_contracts: setupData?.alternative_render_contracts,
              ta_layers: setupData?.ta_layers,
              active_range: setupData?.active_range,
              v2_triggers: patternV2?.trigger || null,
            }}
            // TA MODE — controls layer visibility (Auto/Classic/Smart/Minimal)
            mode={viewMode}
            // TRADE SETUP — generated from confluence analysis (toggle with showSetupOverlay)
            tradeSetupOverlay={showSetupOverlay ? generatedTradeSetup : null}
            // Legacy props for backward compatibility
            pattern={pattern}
            levels={levels}
            setup={setup}
            structure={structureContext || structure}
            baseLayer={baseLayer}
            structureVisualization={structureVisualization}
            chartStructure={chartStructure}
            tradeSetup={tradeSetup}
            // Market Mechanics - use limited data based on visibility
            poi={layerVisibilityComputed.poi ? (poi || limitedPOI) : null}
            liquidity={layerVisibilityComputed.liquidity ? (liquidity || limitedLiquidity) : null}
            chochValidation={layerVisibilityComputed.choch ? chochValidation : null}
            displacement={layerVisibilityComputed.displacement ? displacement : null}
            // NEW: Execution layer from per-TF pipeline
            execution={execution}
            chainMap={chainMap}
            chartType={chartType}
            height={420}
            showLevels={showLevels}
            showPattern={showPatterns && layerVisibilityComputed.pattern_primary}
            showBaseLayer={showBaseLayer}
            showStructure={showStructure}
            showTargets={false}
            showExecutionOverlay={patternViewMode ? false : (execution?.valid || layerVisibilityComputed.trade_setup)}
            // Market Mechanics toggles - HIDDEN in Pattern View mode
            showMarketMechanics={showMarketMechanicsComputed}
            showPOI={showPOIComputed}
            showLiquidity={showLiquidityComputed}
            showSweeps={showSweepsComputed}
            showCHOCH={showCHOCHComputed}
            showNarrative={patternViewMode ? false : (viewMode !== 'minimal')}
            decision={decision}
            // Indicator Overlays - HIDDEN in Pattern View mode
            indicatorOverlays={
              patternViewMode ? [] : (
                layerVisibilityComputed.indicators_overlay
                  ? (setupData?.indicators?.overlays || [])
                      .filter(o => {
                        return selectedOverlays.includes(o.id);
                      })
                      .slice(0, limits.overlays)
                  : []
              )
            }
            // Pattern Engine V2 - USE UNIFIED primaryPattern (from render_contract if available)
            patternV2={{ primary_pattern: primaryPattern, alternative_patterns: alternativePatterns }}
            // Pattern Geometry - DISABLED when V4 render contract available
            patternGeometry={setupData?.pattern_render_contract ? null : setupData?.pattern_geometry}
            // Fibonacci - use from per-TF pipeline
            fibonacci={fib || setupData?.fibonacci}
            // Toggle overlays visibility via buttons
            showFibonacciOverlay={patternViewMode ? false : showFibonacciOverlay}
            showPatternOverlay={showPatternOverlay}
            // Pattern View Mode — for zoom to pattern window
            patternViewMode={patternViewMode}
            patternWindow={patternV2?.renderContract?.window || setupData?.pattern_render_contract?.window}
          />
          {loading && (
            <LoadingOverlay>
              <Loader2 size={24} color="#3b82f6" />
              <span style={{ color: '#64748b', fontSize: 13 }}>Analyzing {symbol}...</span>
            </LoadingOverlay>
          )}
          
          {/* ═══════════════════════════════════════════════════════════════ */}
          {/* RENDER PLAN OVERLAY — TA visualization (moved from Chart Lab) */}
          {/* This is the ONLY place for TA renderers per product rules */}
          {/* ═══════════════════════════════════════════════════════════════ */}
          {showTAOverlay && (globalRenderPlan || renderPlan) && (
            <RenderPlanOverlay 
              renderPlan={globalRenderPlan || renderPlan}
              onChainStepClick={(step) => console.log('[Research/TA] Step clicked:', step)}
            />
          )}
          
        </ChartSection>
        
        {/* ═══════════════════════════════════════════════════════════════ */}
        {/* PATTERN V2 STATE CARD — Decision-grade: state + triggers + action */}
        {/* Shows 1 strongest pattern, its triggers, and its state */}
        {/* ═══════════════════════════════════════════════════════════════ */}
        {patternV2 ? (
          <PatternStateCard pattern={patternV2} data-testid="pattern-state-card" />
        ) : (
          <PatternHintCard
            pattern={setupData?.pattern_render_contract}
            analysisMode={analysisMode}
            summary={setupData?.final_analysis?.summary}
          />
        )}
        
        {/* ═══════════════════════════════════════════════════════════════ */}
        {/* INDICATOR CONTROL BAR — Click to toggle pane visibility */}
        {/* ═══════════════════════════════════════════════════════════════ */}
        {setupData?.indicator_insights && (
          <IndicatorControlBar 
            insights={setupData.indicator_insights}
            activeIndicators={activeIndicators}
            onToggle={handleIndicatorToggle}
          />
        )}
        
        {/* ═══════════════════════════════════════════════════════════════ */}
        {/* STORY LINE — Market Narrative Chain (connects graph + analysis) */}
        {/* ═══════════════════════════════════════════════════════════════ */}
        <StoryLine 
          liquidity={setupData?.liquidity}
          displacement={setupData?.displacement}
          chochValidation={setupData?.choch_validation}
          structure={setupData?.structure}
          decision={decision}
          pattern={primaryPattern}
        />
        
        {/* ═══════════════════════════════════════════════════════════════ */}
        {/* OSCILLATOR PANES — Only show when card is clicked */}
        {/* ═══════════════════════════════════════════════════════════════ */}
        {(activeIndicators.rsi || activeIndicators.macd) && setupData?.indicators?.panes?.length > 0 && (
          <BottomSection style={{ marginTop: '4px' }}>
            <IndicatorPanes 
              indicators={setupData.indicators}
              visiblePanes={Object.entries(activeIndicators).filter(([_, v]) => v).map(([k]) => k)}
              paneHeight={85}
            />
          </BottomSection>
        )}


        {/* ════════════════════════════════════════════════════════════════ */}
        {/* TA LAYERS PANEL — 10 Layer Decision System (NEW!) */}
        {/* ════════════════════════════════════════════════════════════════ */}
        {setupData?.ta_layers && (
          <TALayersPanel
            taLayers={setupData.ta_layers}
            probability={setupData.probability}
            scenarios={setupData.scenarios}
            activeRange={setupData.active_range}
          />
        )}

        {/* ════════════════════════════════════════════════════════════════ */}
        {/* TA EXPLORER — Full Audit Mode (patterns_all, rejected, 10 layers) */}
        {/* ════════════════════════════════════════════════════════════════ */}
        {setupData?.ta_explorer && (
          <TAExplorerPanel data={setupData.ta_explorer} />
        )}


        {/* ════════════════════════════════════════════════════════════════ */}
        {/* UNIFIED ANALYSIS BAR — Context + Setup (P2: COMPACT) */}
        {/* ════════════════════════════════════════════════════════════════ */}
        {decision && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '10px',
            margin: '10px 0',
          }}>
            {/* LEFT: Market Context Summary */}
            <div style={{
              background: '#fff',
              border: '1px solid #e2e8f0',
              borderRadius: '10px',
              padding: '12px 14px',
            }}>
              <div style={{
                fontSize: '10px',
                fontWeight: '700',
                color: '#64748b',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '10px',
              }}>
                Market Context — {selectedTF}
              </div>
              
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '12px',
              }}>
                {/* Bias */}
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '10px', color: '#94a3b8', marginBottom: '4px' }}>BIAS</div>
                  <div style={{
                    fontSize: '14px',
                    fontWeight: '700',
                    color: decision.bias === 'bullish' ? '#16a34a' :
                           decision.bias === 'bearish' ? '#dc2626' : '#64748b',
                  }}>
                    {(decision.bias || 'neutral').toUpperCase()}
                  </div>
                </div>
                
                {/* Confidence */}
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '10px', color: '#94a3b8', marginBottom: '4px' }}>CONFIDENCE</div>
                  <div style={{
                    fontSize: '14px',
                    fontWeight: '700',
                    color: decision.confidence >= 0.6 ? '#16a34a' :
                           decision.confidence >= 0.4 ? '#f59e0b' : '#64748b',
                  }}>
                    {Math.round((decision.confidence || 0) * 100)}%
                  </div>
                </div>
                
                {/* Strength */}
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '10px', color: '#94a3b8', marginBottom: '4px' }}>STRENGTH</div>
                  <div style={{
                    fontSize: '14px',
                    fontWeight: '700',
                    color: decision.strength === 'high' ? '#16a34a' :
                           decision.strength === 'medium' ? '#f59e0b' : '#94a3b8',
                  }}>
                    {(decision.strength || 'low').toUpperCase()}
                  </div>
                </div>
              </div>
              
              {/* Summary text — Research language (use interpretation if available) */}
              {(setupData?.interpretation || decision?.summary) && (
                <div style={{
                  marginTop: '12px',
                  padding: '10px',
                  background: '#f8fafc',
                  borderRadius: '8px',
                  fontSize: '12px',
                  color: '#475569',
                  lineHeight: '1.5',
                }}>
                  {/* Prefer interpretation from backend, fallback to decision.summary with transforms */}
                  {setupData?.interpretation || (decision.summary
                    .replace(/watch long/gi, 'bullish conditions developing')
                    .replace(/watch short/gi, 'bearish conditions developing')
                    .replace(/look for long entries/gi, 'upside momentum forming')
                    .replace(/look for short entries/gi, 'downside pressure')
                    .replace(/no clear action/gi, 'No clear directional signal')
                    .replace(/observe and wait/gi, 'Structure remains mixed')
                    .replace(/tradeability/gi, 'setup quality')
                    .replace(/no trade/gi, 'structure developing')
                    .replace(/invalid/gi, 'not yet confirmed')
                  )}
                </div>
              )}
            </div>
            
            {/* RIGHT: Pattern & Structure — COMPACT */}
            <div style={{
              background: '#fff',
              border: '1px solid #e2e8f0',
              borderRadius: '10px',
              padding: '12px 14px',
            }}>
              <div style={{
                fontSize: '10px',
                fontWeight: '700',
                color: '#64748b',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '10px',
              }}>
                Technical Setup
              </div>
              
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '8px',
              }}>
                {/* Pattern */}
                <div style={{
                  background: '#f8fafc',
                  borderRadius: '6px',
                  padding: '8px 10px',
                }}>
                  <div style={{ fontSize: '9px', color: '#94a3b8', marginBottom: '3px', textTransform: 'uppercase' }}>Pattern</div>
                  <div style={{
                    fontSize: '12px',
                    fontWeight: '600',
                    color: primaryPattern?.type ? '#0f172a' : '#94a3b8',
                  }}>
                    {primaryPattern?.type?.replace(/_/g, ' ') || 'None'}
                  </div>
                  {primaryPattern?.direction && (
                    <div style={{
                      fontSize: '9px',
                      marginTop: '2px',
                      fontWeight: '600',
                      color: primaryPattern.direction === 'bullish' ? '#16a34a' : 
                             primaryPattern.direction === 'bearish' ? '#dc2626' : '#64748b',
                    }}>
                      {primaryPattern.direction.toUpperCase()}
                    </div>
                  )}
                </div>
                
                {/* Levels Count */}
                <div style={{
                  background: '#f8fafc',
                  borderRadius: '6px',
                  padding: '8px 10px',
                }}>
                  <div style={{ fontSize: '9px', color: '#94a3b8', marginBottom: '3px', textTransform: 'uppercase' }}>Levels</div>
                  <div style={{
                    fontSize: '12px',
                    fontWeight: '600',
                    color: '#0f172a',
                  }}>
                    {levels?.length || 0} active
                  </div>
                  <div style={{ fontSize: '9px', marginTop: '2px', color: '#64748b' }}>
                    {levels?.filter(l => l.type === 'support').length || 0}S / {levels?.filter(l => l.type === 'resistance').length || 0}R
                  </div>
                </div>
              </div>
              
              {/* Setup Quality Badge */}
              <div style={{
                marginTop: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}>
                <span style={{ fontSize: '11px', color: '#94a3b8' }}>Setup Quality</span>
                <span style={{
                  fontSize: '11px',
                  fontWeight: '600',
                  padding: '4px 10px',
                  borderRadius: '4px',
                  background: decision.tradeability === 'high' ? 'rgba(34, 197, 94, 0.1)' :
                             decision.tradeability === 'medium' ? 'rgba(245, 158, 11, 0.1)' :
                             'rgba(239, 68, 68, 0.1)',
                  color: decision.tradeability === 'high' ? '#16a34a' :
                         decision.tradeability === 'medium' ? '#f59e0b' : '#dc2626',
                }}>
                  {(decision.tradeability || 'low').toUpperCase()}
                </span>
              </div>
              
              {/* Key Insight */}
              {levels?.length > 0 && (
                <div style={{
                  marginTop: '10px',
                  padding: '8px 10px',
                  background: '#f0f9ff',
                  borderRadius: '6px',
                  fontSize: '11px',
                  color: '#0369a1',
                  fontWeight: '500',
                }}>
                  {(() => {
                    const resistances = levels?.filter(l => l.type === 'resistance') || [];
                    const supports = levels?.filter(l => l.type === 'support') || [];
                    const currentPrice = setupData?.current_price || 0;
                    
                    if (resistances.length > 0 && currentPrice) {
                      const nearestR = resistances.reduce((a, b) => 
                        Math.abs(b.price - currentPrice) < Math.abs(a.price - currentPrice) ? b : a
                      );
                      return `Resistance at ${Math.round(nearestR.price)} defines upside risk`;
                    }
                    if (supports.length > 0 && currentPrice) {
                      const nearestS = supports.reduce((a, b) => 
                        Math.abs(b.price - currentPrice) < Math.abs(a.price - currentPrice) ? b : a
                      );
                      return `Support at ${Math.round(nearestS.price)} defines downside risk`;
                    }
                    return 'Structure and levels being analyzed';
                  })()}
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* NARRATIVE SUMMARY — Market Story Chain (includes Why reasoning) */}
        {!loading && decision && (
          <NarrativeSummary
            narrative={buildNarrative({
              liquidity,
              displacement,
              chochValidation,
              poi,
              decision,
              tradeSetup,
            })}
            decision={decision}
          />
        )}

        {/* UNIFIED SETUP + EXECUTION GRID */}
        {(setupData?.unified_setup || setupData?.execution_plan) && (
          <BottomGrid>
            {/* Left: Unified Setup — Validation Chain */}
            <UnifiedSetupPanel unifiedSetup={setupData.unified_setup} />
            
            {/* Right: Execution Plan — Prop-Trader Execution */}
            <ExecutionPanel executionPlan={setupData.execution_plan} />
          </BottomGrid>
        )}

        {/* PATTERNS + SCENARIOS GRID - NEW */}
        <BottomGrid>
          {/* Left: TA Composition — TECHNICAL SETUP VIEW */}
          <TACompositionPanel composition={taComposition} />
          
          {/* Right: Scenarios */}
          <ScenariosBlock
            scenarios={scenarios}
            onScenarioClick={handleScenarioClick}
          />
        </BottomGrid>
        
        {/* PATTERNS BLOCK — Below main grid */}
        <BottomSection>
          <PatternsBlock
            primaryPattern={primaryPattern}
            alternativePatterns={alternativePatterns}
            activePatternId={activePatternId}
            onPatternClick={handlePatternClick}
          />
        </BottomSection>

        {/* EXPLANATION PANEL — System Explanation (from Explanation Engine V1) */}
        <ExplanationPanel explanation={explanation} />
        
        {/* CONFLUENCE MATRIX — Hidden in minimal mode */}
        {/* Build confluence from taContext indicators for ConfluenceMatrix component */}
        {/* Now includes TA Brain expandable section */}
        {viewMode !== 'minimal' && taContext && (
          <BottomSection>
            <ConfluenceMatrix 
              confluence={{
                bullish: taContext.top_drivers?.filter(d => d.signal === 'bullish') || [],
                bearish: taContext.top_drivers?.filter(d => d.signal === 'bearish') || [],
                neutral: taContext.top_drivers?.filter(d => d.signal === 'neutral') || [],
                conflicts: [],
                overall_strength: taContext.summary?.aggregated_score || 0,
                overall_bias: taContext.summary?.aggregated_bias || 'neutral',
                confidence: taContext.summary?.aggregated_confidence || 0,
                summary: `${taContext.indicators?.bullish || 0} bullish, ${taContext.indicators?.bearish || 0} bearish signals`,
              }}
              taContext={taContext}
            />
          </BottomSection>
        )}

        {/* CONFIDENCE EXPLANATION - NEW */}
        <BottomSection>
          <ConfidenceExplanation explanation={confidenceExplanation} />
        </BottomSection>

        {/* Pattern Activation Layer */}
        <PatternActivationLayer
          setup={unifiedSetup}
          activeElements={activeElements}
          onToggleElement={handleToggleElement}
        />

        {/* Deep Analysis Blocks */}
        <DeepAnalysisBlocks
          setup={unifiedSetup}
          technicalBias={technicalBias}
          biasConfidence={biasConfidence}
        />
      </MainContent>

      {/* Toast */}
      {toast && <SuccessToast>{toast}</SuccessToast>}
    </Container>
  );
};

export default ResearchView;
