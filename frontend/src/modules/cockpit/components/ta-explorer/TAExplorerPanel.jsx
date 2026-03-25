/**
 * TAExplorerPanel.jsx — Full TA Audit Mode
 * 
 * Shows ALL analysis, not just dominant:
 * - Dominant pattern with why_selected
 * - All detected patterns ranked
 * - Rejected patterns
 * - All 10 TA layers
 * - Trade Setup (ONLY when CLEAR)
 */

import React, { useState } from 'react';
import styled from 'styled-components';
import DominantCard from './DominantCard';
import PatternsList from './PatternsList';
import RejectedList from './RejectedList';
import LayersTable from './LayersTable';
import TradeSetupCard from './TradeSetupCard';

const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.1);
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
`;

const Title = styled.h3`
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const Badge = styled.span`
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
`;

const Tabs = styled.div`
  display: flex;
  gap: 4px;
  background: rgba(15, 23, 42, 0.8);
  padding: 4px;
  border-radius: 6px;
`;

const Tab = styled.button`
  padding: 6px 12px;
  font-size: 11px;
  font-weight: 500;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  background: ${props => props.$active ? 'rgba(59, 130, 246, 0.3)' : 'transparent'};
  color: ${props => props.$active ? '#3b82f6' : '#94a3b8'};
  
  &:hover {
    background: ${props => props.$active ? 'rgba(59, 130, 246, 0.3)' : 'rgba(148, 163, 184, 0.1)'};
  }
`;

const Content = styled.div`
  min-height: 200px;
`;

const NoData = styled.div`
  color: #64748b;
  font-size: 12px;
  text-align: center;
  padding: 40px;
`;

export default function TAExplorerPanel({ data }) {
  const [activeTab, setActiveTab] = useState('overview');
  
  if (!data) {
    return (
      <Container>
        <NoData>Loading TA Explorer...</NoData>
      </Container>
    );
  }
  
  const { dominant, patterns_all, patterns_rejected, ta_layers, trade_setup } = data;
  
  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <>
            <DominantCard dominant={dominant} />
            <PatternsList 
              patterns={patterns_all} 
              title="All Detected" 
              showAll={false}
            />
            {/* Trade Setup — ONLY when available (CLEAR confidence) */}
            <TradeSetupCard setup={trade_setup} />
          </>
        );
      
      case 'patterns':
        return (
          <>
            <PatternsList 
              patterns={patterns_all} 
              title="All Detected Patterns" 
              showAll={true}
            />
            <RejectedList rejected={patterns_rejected} />
          </>
        );
      
      case 'layers':
        return <LayersTable layers={ta_layers} />;
      
      case 'trade':
        return <TradeSetupCard setup={trade_setup} />;
      
      default:
        return null;
    }
  };
  
  // Check if trade is available for badge
  const isTradeAvailable = trade_setup?.available === true;
  
  return (
    <Container data-testid="ta-explorer-panel">
      <Header>
        <Title>
          TA Explorer
          <Badge>AUDIT</Badge>
        </Title>
        
        <Tabs>
          <Tab 
            $active={activeTab === 'overview'} 
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </Tab>
          <Tab 
            $active={activeTab === 'patterns'} 
            onClick={() => setActiveTab('patterns')}
          >
            Patterns ({patterns_all?.length || 0})
          </Tab>
          <Tab 
            $active={activeTab === 'layers'} 
            onClick={() => setActiveTab('layers')}
          >
            10 Layers
          </Tab>
          <Tab 
            $active={activeTab === 'trade'} 
            onClick={() => setActiveTab('trade')}
            style={{ 
              color: isTradeAvailable ? '#22c55e' : '#f87171',
              fontWeight: isTradeAvailable ? 600 : 400,
            }}
          >
            {isTradeAvailable ? 'TRADE' : 'No Trade'}
          </Tab>
        </Tabs>
      </Header>
      
      <Content>
        {renderContent()}
      </Content>
    </Container>
  );
}
