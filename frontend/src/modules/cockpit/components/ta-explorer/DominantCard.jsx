/**
 * DominantCard.jsx — Shows dominant pattern/range with why_selected + confidence_state
 */

import React from 'react';
import styled from 'styled-components';

const Card = styled.div`
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid ${props => 
    props.$state === 'clear' ? 'rgba(34, 197, 94, 0.4)' : 
    props.$state === 'conflicted' ? 'rgba(239, 68, 68, 0.4)' : 
    'rgba(59, 130, 246, 0.3)'
  };
  border-radius: 8px;
  padding: 12px;
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
`;

const Label = styled.span`
  font-size: 10px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const Score = styled.span`
  font-size: 12px;
  font-weight: 600;
  color: ${props => props.$score > 75 ? '#22c55e' : props.$score > 50 ? '#eab308' : '#94a3b8'};
`;

const Title = styled.div`
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 4px;
`;

const Meta = styled.div`
  font-size: 11px;
  color: #94a3b8;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
`;

const ModeBadge = styled.span`
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
  background: ${props => 
    props.$mode === 'strict' ? 'rgba(34, 197, 94, 0.2)' : 
    props.$mode === 'regime' ? 'rgba(59, 130, 246, 0.2)' : 
    'rgba(148, 163, 184, 0.2)'
  };
  color: ${props => 
    props.$mode === 'strict' ? '#22c55e' : 
    props.$mode === 'regime' ? '#3b82f6' : 
    '#94a3b8'
  };
`;

const BiasBadge = styled.span`
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
  background: ${props => 
    props.$bias === 'bullish' ? 'rgba(34, 197, 94, 0.2)' : 
    props.$bias === 'bearish' ? 'rgba(239, 68, 68, 0.2)' : 
    'rgba(148, 163, 184, 0.2)'
  };
  color: ${props => 
    props.$bias === 'bullish' ? '#22c55e' : 
    props.$bias === 'bearish' ? '#ef4444' : 
    '#94a3b8'
  };
`;

const ConfidenceBadge = styled.span`
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  background: ${props => 
    props.$state === 'clear' ? 'rgba(34, 197, 94, 0.2)' : 
    props.$state === 'conflicted' ? 'rgba(239, 68, 68, 0.2)' : 
    props.$state === 'weak' ? 'rgba(234, 179, 8, 0.2)' : 
    'rgba(148, 163, 184, 0.2)'
  };
  color: ${props => 
    props.$state === 'clear' ? '#22c55e' : 
    props.$state === 'conflicted' ? '#ef4444' : 
    props.$state === 'weak' ? '#eab308' : 
    '#94a3b8'
  };
`;

const WhySection = styled.div`
  border-top: 1px solid rgba(148, 163, 184, 0.1);
  padding-top: 8px;
`;

const WhyLabel = styled.div`
  font-size: 10px;
  color: #64748b;
  margin-bottom: 4px;
`;

const WhyList = styled.ul`
  margin: 0;
  padding: 0 0 0 16px;
  font-size: 11px;
  color: #94a3b8;
  
  li {
    margin-bottom: 2px;
  }
  
  li.warning {
    color: #f87171;
  }
  
  li.positive {
    color: #22c55e;
  }
`;

const ComponentsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 4px;
  margin-top: 8px;
  font-size: 9px;
`;

const ComponentItem = styled.div`
  text-align: center;
  padding: 4px;
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.05);
  
  .label {
    color: #64748b;
    margin-bottom: 2px;
  }
  
  .value {
    font-weight: 600;
    color: ${props => 
      props.$value > 0 ? '#22c55e' : 
      props.$value < 0 ? '#ef4444' : 
      '#94a3b8'
    };
  }
`;

const NoData = styled.div`
  color: #64748b;
  font-size: 12px;
  padding: 20px;
  text-align: center;
`;

export default function DominantCard({ dominant }) {
  if (!dominant) {
    return (
      <Card>
        <NoData>No dominant pattern detected</NoData>
      </Card>
    );
  }
  
  const formatType = (type) => {
    return type
      .replace(/_/g, ' ')
      .replace(/\b\w/g, c => c.toUpperCase());
  };
  
  const components = dominant.components || {};
  const confidenceState = dominant.confidence_state || 'unknown';
  const score = dominant.score || 0;
  
  return (
    <Card $state={confidenceState} data-testid="dominant-card">
      <Header>
        <Label>Dominant</Label>
        <Score $score={score}>
          {score.toFixed(0)}
        </Score>
      </Header>
      
      <Title>{formatType(dominant.type)}</Title>
      
      <Meta>
        <ModeBadge $mode={dominant.mode}>{dominant.mode}</ModeBadge>
        <BiasBadge $bias={dominant.bias}>{dominant.bias}</BiasBadge>
        <ConfidenceBadge $state={confidenceState}>
          {confidenceState === 'clear' ? 'CLEAR' : 
           confidenceState === 'conflicted' ? 'CONFLICTED' : 
           confidenceState === 'weak' ? 'WEAK' : 
           confidenceState.toUpperCase()}
        </ConfidenceBadge>
        <span>{dominant.stage}</span>
      </Meta>
      
      {/* Components breakdown */}
      {Object.keys(components).length > 0 && (
        <ComponentsGrid>
          <ComponentItem $value={components.base || 0}>
            <div className="label">Base</div>
            <div className="value">{(components.base || 0).toFixed(0)}</div>
          </ComponentItem>
          <ComponentItem $value={components.structure || 0}>
            <div className="label">Struct</div>
            <div className="value">{(components.structure || 0) > 0 ? '+' : ''}{(components.structure || 0).toFixed(0)}</div>
          </ComponentItem>
          <ComponentItem $value={components.htf || 0}>
            <div className="label">HTF</div>
            <div className="value">{(components.htf || 0) > 0 ? '+' : ''}{(components.htf || 0).toFixed(0)}</div>
          </ComponentItem>
          <ComponentItem $value={components.regime || 0}>
            <div className="label">Regime</div>
            <div className="value">{(components.regime || 0) > 0 ? '+' : ''}{(components.regime || 0).toFixed(0)}</div>
          </ComponentItem>
          <ComponentItem $value={components.conflict || 0}>
            <div className="label">Conflict</div>
            <div className="value">{(components.conflict || 0).toFixed(0)}</div>
          </ComponentItem>
        </ComponentsGrid>
      )}
      
      {dominant.why_selected?.length > 0 && (
        <WhySection>
          <WhyLabel>Why selected:</WhyLabel>
          <WhyList>
            {dominant.why_selected.map((reason, i) => (
              <li 
                key={i}
                className={
                  reason.includes('WARNING') ? 'warning' : 
                  reason.includes('Strong') ? 'positive' : 
                  ''
                }
              >
                {reason}
              </li>
            ))}
          </WhyList>
        </WhySection>
      )}
    </Card>
  );
}
