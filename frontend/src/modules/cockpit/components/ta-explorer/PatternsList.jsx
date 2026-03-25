/**
 * PatternsList.jsx — Shows all detected patterns ranked by FINAL score (V2)
 */

import React from 'react';
import styled from 'styled-components';

const Card = styled.div`
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(148, 163, 184, 0.1);
  border-radius: 8px;
  padding: 12px;
`;

const Header = styled.div`
  font-size: 12px;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 8px;
`;

const Row = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px;
  border-radius: 4px;
  margin-bottom: 4px;
  background: ${props => props.$isFirst ? 'rgba(59, 130, 246, 0.1)' : 'transparent'};
  border-left: 2px solid ${props => props.$isFirst ? '#3b82f6' : 'transparent'};
  
  &:hover {
    background: rgba(148, 163, 184, 0.05);
  }
`;

const Left = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`;

const Rank = styled.span`
  font-size: 10px;
  color: #64748b;
  width: 16px;
`;

const Type = styled.span`
  font-size: 12px;
  font-weight: 500;
  color: #f1f5f9;
`;

const ModeBadge = styled.span`
  font-size: 9px;
  padding: 2px 4px;
  border-radius: 3px;
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
  font-size: 9px;
  padding: 2px 4px;
  border-radius: 3px;
  background: ${props => 
    props.$bias === 'bullish' ? 'rgba(34, 197, 94, 0.15)' : 
    props.$bias === 'bearish' ? 'rgba(239, 68, 68, 0.15)' : 
    'transparent'
  };
  color: ${props => 
    props.$bias === 'bullish' ? '#22c55e' : 
    props.$bias === 'bearish' ? '#ef4444' : 
    '#64748b'
  };
`;

const Right = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const ScoreGroup = styled.div`
  display: flex;
  flex-direction: column;
  align-items: flex-end;
`;

const FinalScore = styled.span`
  font-size: 12px;
  font-weight: 600;
  color: ${props => props.$score > 75 ? '#22c55e' : props.$score > 50 ? '#eab308' : '#94a3b8'};
`;

const BaseScore = styled.span`
  font-size: 9px;
  color: #64748b;
`;

const Stage = styled.span`
  font-size: 10px;
  color: #64748b;
  min-width: 50px;
  text-align: right;
`;

const NoData = styled.div`
  color: #64748b;
  font-size: 11px;
  padding: 16px;
  text-align: center;
`;

export default function PatternsList({ patterns, title = "Detected Patterns", showAll = false }) {
  if (!patterns?.length) {
    return (
      <Card>
        <Header>{title}</Header>
        <NoData>No patterns detected</NoData>
      </Card>
    );
  }
  
  const displayPatterns = showAll ? patterns : patterns.slice(0, 3);
  
  const formatType = (type) => {
    return type
      .replace(/_/g, ' ')
      .replace(/\b\w/g, c => c.toUpperCase());
  };
  
  return (
    <Card data-testid="patterns-list">
      <Header>{title}</Header>
      
      {displayPatterns.map((pattern, index) => {
        // Use final_score if available (V2), otherwise fall back to score
        const finalScore = pattern.final_score ?? (pattern.score <= 1 ? pattern.score * 100 : pattern.score);
        const baseScore = pattern.base_score ?? (pattern.score <= 1 ? pattern.score * 100 : pattern.score);
        
        return (
          <Row key={index} $isFirst={index === 0}>
            <Left>
              <Rank>#{index + 1}</Rank>
              <Type>{formatType(pattern.type)}</Type>
              <ModeBadge $mode={pattern.mode}>{pattern.mode}</ModeBadge>
              <BiasBadge $bias={pattern.bias}>{pattern.bias}</BiasBadge>
            </Left>
            
            <Right>
              <ScoreGroup>
                <FinalScore $score={finalScore}>
                  {finalScore.toFixed(0)}
                </FinalScore>
                {pattern.final_score && pattern.base_score && (
                  <BaseScore>base: {baseScore.toFixed(0)}</BaseScore>
                )}
              </ScoreGroup>
              <Stage>{pattern.stage}</Stage>
            </Right>
          </Row>
        );
      })}
      
      {!showAll && patterns.length > 3 && (
        <NoData>+{patterns.length - 3} more patterns</NoData>
      )}
    </Card>
  );
}
