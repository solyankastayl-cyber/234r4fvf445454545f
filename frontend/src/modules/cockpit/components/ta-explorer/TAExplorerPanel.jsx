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
  gap: 16px;
  padding: 20px;
  background: #0f172a;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
`;

const Title = styled.h3`
  font-size: 14px;
  font-weight: 700;
  color: #ffffff;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const Badge = styled.span`
  font-size: 10px;
  padding: 3px 8px;
  border-radius: 4px;
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
  font-weight: 600;
`;

const Tabs = styled.div`
  display: flex;
  gap: 4px;
  background: rgba(255, 255, 255, 0.05);
  padding: 4px;
  border-radius: 8px;
`;

const Tab = styled.button`
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 600;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  background: ${props => props.$active ? '#3b82f6' : 'transparent'};
  color: ${props => props.$active ? '#ffffff' : 'rgba(255, 255, 255, 0.6)'};
  
  &:hover {
    background: ${props => props.$active ? '#3b82f6' : 'rgba(255, 255, 255, 0.1)'};
    color: #ffffff;
  }
`;

const Content = styled.div`
  min-height: 200px;
`;

const NoData = styled.div`
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
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
