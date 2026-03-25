import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { TrendingUp, TrendingDown, Zap, AlertTriangle, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { useMarket, useHypotheses, useSignalExplanation } from '../../../store/marketStore';
import ResearchService from '../../../services/researchService';
import IdeasPanel from '../components/IdeasPanel';

// ============================================
// STYLED COMPONENTS
// ============================================

const Container = styled.div`
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 20px;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const MainColumn = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const SideColumn = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
  
  @media (max-width: 1200px) {
    order: -1;
  }
`;

const LoadingContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #738094;
  
  svg {
    animation: spin 1s linear infinite;
    margin-right: 12px;
  }
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

const TopHypothesis = styled.div`
  background: #ffffff;
  border: 2px solid #05A584;
  border-radius: 16px;
  overflow: hidden;
`;

const TopHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #eef1f5;
`;

const TopLabel = styled.span`
  padding: 5px 10px;
  background: #e8f9f1;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  color: #05A584;
`;

const TopTitle = styled.span`
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  margin-left: 12px;
`;

const Badge = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  background: ${({ $type }) => $type === 'long' ? '#e8f9f1' : 'rgba(239, 68, 68, 0.1)'};
  color: ${({ $type }) => $type === 'long' ? '#05A584' : '#ef4444'};
`;

const TopContent = styled.div`
  padding: 24px;
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
  
  @media (max-width: 900px) {
    grid-template-columns: repeat(2, 1fr);
  }
`;

const Metric = styled.div`
  .label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #9CA3AF;
    margin-bottom: 6px;
  }
  
  .value {
    font-size: 28px;
    font-weight: 700;
    color: ${({ $color }) => $color || '#0f172a'};
  }
`;

const AlignmentGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 24px;
  
  @media (max-width: 900px) {
    grid-template-columns: 1fr;
  }
`;

const AlignmentItem = styled.div`
  .header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
  }
  
  .label {
    font-size: 13px;
    color: #738094;
  }
  
  .value {
    font-size: 14px;
    font-weight: 600;
    color: #0f172a;
  }
`;

const ProgressBar = styled.div`
  height: 6px;
  background: #eef1f5;
  border-radius: 3px;
  overflow: hidden;
  
  .fill {
    height: 100%;
    background: #05A584;
    border-radius: 3px;
    width: ${({ $value }) => Math.min($value, 100)}%;
    transition: width 0.3s ease;
  }
`;

const ExplanationSection = styled.div`
  margin-bottom: 20px;
`;

const SectionTitle = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: ${({ $color }) => $color || '#05A584'};
  margin-bottom: 10px;
`;

const ExplanationText = styled.div`
  font-size: 15px;
  color: #0f172a;
  line-height: 1.6;
`;

const ConflictBox = styled.div`
  padding: 16px;
  background: rgba(245, 158, 11, 0.08);
  border-radius: 10px;
  border: 1px solid rgba(245, 158, 11, 0.15);
`;

const ConflictItem = styled.div`
  font-size: 14px;
  color: #738094;
  margin-bottom: 6px;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const Actions = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
`;

const Button = styled.button`
  padding: 10px 20px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.15s;
  
  ${({ $variant }) => $variant === 'primary' 
    ? 'background: #05A584; color: white; &:hover { background: #048a6e; }'
    : 'background: #f5f7fa; color: #738094; &:hover { background: #eef1f5; }'
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const CompetingSection = styled.div`
  margin-top: 16px;
`;

const SectionHeader = styled.div`
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #9CA3AF;
  margin-bottom: 12px;
`;

const HypothesisList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const HypothesisCard = styled.div`
  background: #ffffff;
  border: 1px solid #eef1f5;
  border-radius: 12px;
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.15s;
  
  &:hover {
    border-color: #05A584;
    box-shadow: 0 2px 8px rgba(5, 165, 132, 0.08);
  }
`;

const CardHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
`;

const CardTitle = styled.span`
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
`;

const CardMetrics = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
`;

const CardMetric = styled.div`
  .label {
    font-size: 10px;
    text-transform: uppercase;
    color: #9CA3AF;
    margin-bottom: 2px;
  }
  
  .value {
    font-size: 15px;
    font-weight: 600;
    color: #0f172a;
  }
`;

const DecayBadge = styled.span`
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 4px;
  background: ${({ $stage }) => {
    switch ($stage) {
      case 'FRESH': return '#e8f9f1';
      case 'MATURE': return 'rgba(245, 158, 11, 0.1)';
      case 'DECAYING': return 'rgba(239, 68, 68, 0.1)';
      default: return '#f5f7fa';
    }
  }};
  color: ${({ $stage }) => {
    switch ($stage) {
      case 'FRESH': return '#05A584';
      case 'MATURE': return '#f59e0b';
      case 'DECAYING': return '#ef4444';
      default: return '#738094';
    }
  }};
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 40px;
  color: #738094;
  background: #ffffff;
  border: 1px solid #eef1f5;
  border-radius: 12px;
`;

// ============================================
// COMPONENT
// ============================================

const HypothesesView = () => {
  const { loading } = useMarket();
  const hypotheses = useHypotheses();
  const signal = useSignalExplanation();
  const [expanded, setExpanded] = useState(null);
  const [selectedHypothesis, setSelectedHypothesis] = useState(null);

  const top = hypotheses.top;
  const list = hypotheses.list || [];
  const otherHypotheses = list.filter(h => h.hypothesis_id !== top?.hypothesis_id);

  // Load details when expanded
  const handleExpand = async (hypothesis) => {
    if (expanded === hypothesis.hypothesis_id) {
      setExpanded(null);
      setSelectedHypothesis(null);
    } else {
      setExpanded(hypothesis.hypothesis_id);
      // Load full details
      const details = await ResearchService.getHypothesis(hypothesis.hypothesis_id);
      if (details) {
        setSelectedHypothesis(details);
      }
    }
  };

  if (loading && !top) {
    return (
      <LoadingContainer data-testid="hypotheses-view-loading">
        <Loader2 size={24} />
        Loading hypotheses...
      </LoadingContainer>
    );
  }

  if (!top && list.length === 0) {
    return (
      <Container data-testid="hypotheses-view">
        <EmptyState>
          <AlertTriangle size={32} style={{ marginBottom: 12, color: '#f59e0b' }} />
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>No Hypotheses Available</div>
          <div style={{ fontSize: 14 }}>Market analysis is in progress. Check back shortly.</div>
        </EmptyState>
      </Container>
    );
  }

  const getDirectionType = (direction) => {
    if (!direction) return 'neutral';
    const d = direction.toUpperCase();
    return d === 'LONG' || d === 'UP' || d === 'BULLISH' ? 'long' : 'short';
  };

  return (
    <Container data-testid="hypotheses-view">
      <MainColumn>
      {/* Top Hypothesis */}
      {top && (
        <TopHypothesis>
          <TopHeader>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <TopLabel>TOP HYPOTHESIS</TopLabel>
              <TopTitle>{top.name || top.type?.replace(/_/g, ' ') || 'Unknown'}</TopTitle>
              {top.applicableTimeframes && top.applicableTimeframes.length > 0 && (
                <span style={{ marginLeft: 12, fontSize: 11, color: '#9CA3AF' }}>
                  {top.applicableTimeframes.join(', ')}
                </span>
              )}
            </div>
            <Badge $type={getDirectionType(top.direction)}>
              {top.direction === 'LONG' || top.direction === 'UP' ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              {top.direction || 'NEUTRAL'}
            </Badge>
          </TopHeader>
          
          <TopContent>
            <MetricsGrid>
              <Metric $color="#05A584">
                <div className="label">Confidence</div>
                <div className="value">{Math.round(top.confidence || 0)}%</div>
              </Metric>
              <Metric>
                <div className="label">Target Move</div>
                <div className="value">{top.targetMovePct ? `${top.targetMovePct}%` : '—'}</div>
              </Metric>
              <Metric>
                <div className="label">Time Horizon</div>
                <div className="value" style={{ fontSize: 18 }}>{top.timeHorizonCandles ? `${top.timeHorizonCandles} candles` : '—'}</div>
              </Metric>
              <Metric $color="#05A584">
                <div className="label">Alpha Family</div>
                <div className="value" style={{ fontSize: 18 }}>{top.alphaFamily || 'Unknown'}</div>
              </Metric>
            </MetricsGrid>
            
            <AlignmentGrid>
              <AlignmentItem>
                <div className="header">
                  <span className="label">Scenario Alignment</span>
                  <span className="value">{Math.round(top.scenarioAlignment || 0)}%</span>
                </div>
                <ProgressBar $value={top.scenarioAlignment || 0}><div className="fill" /></ProgressBar>
              </AlignmentItem>
              <AlignmentItem>
                <div className="header">
                  <span className="label">Capital Flow</span>
                  <span className="value">{Math.round(top.capitalFlowAlignment || 0)}%</span>
                </div>
                <ProgressBar $value={top.capitalFlowAlignment || 0}><div className="fill" /></ProgressBar>
              </AlignmentItem>
              <AlignmentItem>
                <div className="header">
                  <span className="label">Fractal Match</span>
                  <span className="value">{Math.round(top.fractalAlignment || 0)}%</span>
                </div>
                <ProgressBar $value={top.fractalAlignment || 0}><div className="fill" /></ProgressBar>
              </AlignmentItem>
            </AlignmentGrid>
            
            <ExplanationSection>
              <SectionTitle><Zap size={14} /> Explanation</SectionTitle>
              <ExplanationText>
                {top.explanation || signal.summary || 'Analyzing market conditions to generate explanation...'}
              </ExplanationText>
            </ExplanationSection>
            
            {((top.conflicts && top.conflicts.length > 0) || (signal.conflicts && signal.conflicts.length > 0)) && (
              <ConflictBox>
                <SectionTitle $color="#f59e0b"><AlertTriangle size={14} /> Conflicts</SectionTitle>
                {(top.conflicts || signal.conflicts || []).map((c, i) => (
                  <ConflictItem key={i}>• {typeof c === 'string' ? c : c.name || c.description}</ConflictItem>
                ))}
              </ConflictBox>
            )}
            
            <Actions>
              <Button>View Details</Button>
              <Button $variant="primary" disabled={!top.executionEligibility}>
                Send to Execution
              </Button>
            </Actions>
          </TopContent>
        </TopHypothesis>
      )}
      
      {/* Competing Hypotheses */}
      {otherHypotheses.length > 0 && (
        <CompetingSection>
          <SectionHeader>Competing Hypotheses ({otherHypotheses.length})</SectionHeader>
          <HypothesisList>
            {otherHypotheses.map(hyp => (
              <HypothesisCard key={hyp.hypothesis_id} onClick={() => handleExpand(hyp)}>
                <CardHeader>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <CardTitle>{hyp.name || hyp.type?.replace(/_/g, ' ')}</CardTitle>
                    <Badge $type={getDirectionType(hyp.direction)}>{hyp.direction || 'NEUTRAL'}</Badge>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <DecayBadge $stage={hyp.decayStage}>{hyp.decayStage || 'FRESH'}</DecayBadge>
                    {expanded === hyp.hypothesis_id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </div>
                </CardHeader>
                
                <CardMetrics>
                  <CardMetric>
                    <div className="label">Confidence</div>
                    <div className="value" style={{ color: '#05A584' }}>{Math.round(hyp.confidence || 0)}%</div>
                  </CardMetric>
                  <CardMetric>
                    <div className="label">Target</div>
                    <div className="value">{hyp.targetMovePct ? `${hyp.targetMovePct}%` : '—'}</div>
                  </CardMetric>
                  <CardMetric>
                    <div className="label">Horizon</div>
                    <div className="value">{hyp.timeHorizonCandles ? `${hyp.timeHorizonCandles} candles` : '—'}</div>
                  </CardMetric>
                </CardMetrics>
                
                {expanded === hyp.hypothesis_id && (
                  <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid #eef1f5' }}>
                    <div style={{ fontSize: 14, color: '#738094', lineHeight: 1.5, marginBottom: 12 }}>
                      {selectedHypothesis?.explanation || hyp.explanation || 'Loading details...'}
                    </div>
                    {(selectedHypothesis?.conflicts || hyp.conflicts || []).length > 0 && (
                      <div style={{ fontSize: 13, color: '#f59e0b' }}>
                        Conflicts: {(selectedHypothesis?.conflicts || hyp.conflicts || []).map(c => 
                          typeof c === 'string' ? c : c.name
                        ).join(', ')}
                      </div>
                    )}
                    <Actions style={{ marginTop: 12 }}>
                      <Button style={{ fontSize: 13, padding: '8px 14px' }}>Details</Button>
                      <Button 
                        $variant="primary" 
                        disabled={!(selectedHypothesis?.executionEligibility ?? hyp.executionEligibility)} 
                        style={{ fontSize: 13, padding: '8px 14px' }}
                      >
                        Execute
                      </Button>
                    </Actions>
                  </div>
                )}
              </HypothesisCard>
            ))}
          </HypothesisList>
        </CompetingSection>
      )}
      </MainColumn>
      
      {/* Side Column - Saved Ideas */}
      <SideColumn>
        <IdeasPanel />
      </SideColumn>
    </Container>
  );
};

export default HypothesesView;
