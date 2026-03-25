import React, { useState, useEffect, useCallback } from 'react';
import { 
  Brain, BarChart2,
  TrendingUp, TrendingDown, Zap,
  RefreshCw, Share2, Camera, Bookmark, Check, Loader2
} from 'lucide-react';
import styled from 'styled-components';
import CockpitAPI from './services/api';
import { MarketProvider, useMarket } from '../../store/marketStore';
import setupService from '../../services/setupService';

// ============================================
// STYLED COMPONENTS - Clean Platform Integration
// ============================================

const PageContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: calc(100vh - 64px);
  background: #f5f7fa;
`;

const StatusStrip = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: #ffffff;
  border-bottom: 1px solid #eef1f5;
  gap: 16px;
  flex-wrap: wrap;
`;

const StatusItem = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  
  .label {
    color: #9CA3AF;
  }
  
  .value {
    font-weight: 600;
    color: ${({ $positive }) => $positive === true ? '#05A584' : $positive === false ? '#ef4444' : '#0f172a'};
  }
`;

const StatusBadge = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  background: ${({ $type }) => {
    switch ($type) {
      case 'success': return '#e8f9f1';
      case 'warning': return 'rgba(245, 158, 11, 0.1)';
      case 'danger': return 'rgba(239, 68, 68, 0.1)';
      default: return '#f5f7fa';
    }
  }};
  color: ${({ $type }) => {
    switch ($type) {
      case 'success': return '#05A584';
      case 'warning': return '#f59e0b';
      case 'danger': return '#ef4444';
      default: return '#738094';
    }
  }};
  
  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
    animation: pulse 2s infinite;
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;

const TabsNav = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #ffffff;
  border-bottom: 1px solid #eef1f5;
`;

const TabsGroup = styled.div`
  display: flex;
  gap: 4px;
  padding: 12px 0;
`;

const ActionsGroup = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`;

const ActionBtn = styled.button`
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  color: #64748b;
  
  &:hover:not(:disabled) {
    background: #f8fafc;
    color: #0f172a;
    border-color: #cbd5e1;
  }
  
  &.primary {
    background: #3b82f6;
    color: #ffffff;
    border-color: #3b82f6;
    &:hover:not(:disabled) { background: #2563eb; border-color: #2563eb; }
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  svg { width: 14px; height: 14px; }
  
  .animate-spin {
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

const TabButton = styled.button`
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  border: none;
  background: ${({ $active }) => $active ? '#e8f9f1' : 'transparent'};
  color: ${({ $active }) => $active ? '#05A584' : '#738094'};
  
  &:hover {
    background: ${({ $active }) => $active ? '#e8f9f1' : '#f5f7fa'};
    color: ${({ $active }) => $active ? '#05A584' : '#0f172a'};
  }
  
  svg {
    width: 16px;
    height: 16px;
  }
`;

const TabDivider = styled.div`
  width: 1px;
  height: 24px;
  background: #eef1f5;
  margin: 0 8px;
`;

const AdminLabel = styled.span`
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #9CA3AF;
  margin-right: 8px;
`;

const MainContent = styled.div`
  flex: 1;
  overflow: ${({ $isChart }) => $isChart ? 'hidden' : 'auto'};
  padding: ${({ $isChart }) => $isChart ? '0' : '12px 16px'};
`;

// ============================================
// USER TABS (Research only)
// ============================================

const USER_TABS = [
  { id: 'research', label: 'Research', icon: BarChart2 },
  { id: 'hypotheses', label: 'Hypotheses', icon: Brain }
];

// ============================================
// MAIN COMPONENT (INNER - uses MarketProvider context)
// ============================================

const TechAnalysisInner = () => {
  const [activeTab, setActiveTab] = useState('research');
  const { symbol, researchState, loading, timeframe } = useMarket();
  
  const [systemStatus, setSystemStatus] = useState({
    health: 'HEALTHY',
    mode: 'PAPER',
    equity: 125430.50,
    dailyPnL: 2340.20,
    latency: 45
  });
  
  // Save Idea state
  const [savingIdea, setSavingIdea] = useState(false);
  const [savedIdea, setSavedIdea] = useState(null);
  const [ideaToast, setIdeaToast] = useState(null);

  // Handle Save Idea
  const handleSaveIdea = useCallback(async () => {
    if (savingIdea) return;
    
    try {
      setSavingIdea(true);
      const result = await setupService.createIdea(symbol, timeframe || '4H');
      
      if (result.ok) {
        setSavedIdea(result.idea);
        setIdeaToast(`Idea saved: ${result.idea.idea_id}`);
        setTimeout(() => setIdeaToast(null), 3000);
      }
    } catch (err) {
      console.error('Failed to save idea:', err);
      setIdeaToast('Failed to save idea');
      setTimeout(() => setIdeaToast(null), 3000);
    } finally {
      setSavingIdea(false);
    }
  }, [symbol, timeframe, savingIdea]);

  useEffect(() => {
    // Fetch system status
    const fetchStatus = async () => {
      try {
        const [health, registry] = await Promise.all([
          fetch(`${process.env.REACT_APP_BACKEND_URL || ''}/api/health`).then(r => r.json()),
          CockpitAPI.getTARegistry()
        ]);
        
        if (registry?.status === 'ok') {
          console.log('[TechAnalysis] Loaded registry:', registry.registry?.strategies_count, 'strategies');
        }
        
        // Update status from research state if available
        if (health?.ok) {
          setSystemStatus(prev => ({
            ...prev,
            health: 'HEALTHY',
            latency: health.latency || 45
          }));
        }
      } catch (err) {
        console.log('[TechAnalysis] Using default status');
      }
    };
    fetchStatus();
  }, []);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
  };

  return (
    <PageContainer data-testid="tech-analysis-module">
      {/* Tabs Navigation */}
      <TabsNav data-testid="tabs-nav">
        <TabsGroup>
          {USER_TABS.map(tab => (
            <TabButton
              key={tab.id}
              $active={activeTab === tab.id}
              onClick={() => setActiveTab(tab.id)}
              data-testid={`tab-${tab.id}`}
            >
              <tab.icon />
              {tab.label}
            </TabButton>
          ))}
        </TabsGroup>
        <ActionsGroup>
          <ActionBtn data-testid="header-refresh-btn">
            <RefreshCw /> Refresh
          </ActionBtn>
          <ActionBtn data-testid="header-share-btn">
            <Share2 /> Share
          </ActionBtn>
          <ActionBtn data-testid="header-screenshot-btn">
            <Camera /> Screenshot
          </ActionBtn>
          <ActionBtn className="primary" onClick={handleSaveIdea} disabled={savingIdea} data-testid="header-save-idea-btn">
            {savingIdea ? <Loader2 className="animate-spin" /> : savedIdea ? <Check /> : <Bookmark />}
            {savingIdea ? 'Saving...' : savedIdea ? 'Saved' : 'Save Idea'}
          </ActionBtn>
        </ActionsGroup>
        
        {/* Toast notification */}
        {ideaToast && (
          <div style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            padding: '12px 20px',
            background: '#0f172a',
            color: '#fff',
            borderRadius: '8px',
            fontSize: '13px',
            zIndex: 1000,
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
          }}>
            {ideaToast}
          </div>
        )}
      </TabsNav>
      
      {/* Main Content */}
      <MainContent data-testid="main-content">
        {activeTab === 'research' && <ResearchView />}
        {activeTab === 'hypotheses' && <HypothesesView />}
      </MainContent>
    </PageContainer>
  );
};

// ============================================
// MAIN COMPONENT (WRAPPED WITH PROVIDER)
// ============================================

const TechAnalysisModule = () => {
  return (
    <MarketProvider>
      <TechAnalysisInner />
    </MarketProvider>
  );
};

// ============================================
// VIEW COMPONENTS
// ============================================

// Import views - Light theme with tables and full UI
import ResearchView from './views/ResearchViewNew';
import HypothesesView from './views/HypothesesView';

export default TechAnalysisModule;
