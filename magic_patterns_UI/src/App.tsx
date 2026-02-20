import React, { useState } from 'react';
import { LandingScreen } from './components/LandingScreen';
import { LoadingScreen } from './components/LoadingScreen';
import { VerdictScreen } from './components/VerdictScreen';
import { OutOfScopeScreen } from './components/OutOfScopeScreen';
import { ErrorScreen } from './components/ErrorScreen';
import { MOCK_VERDICTS, OUT_OF_SCOPE_CLAIM } from './utils/mockData';
type AppState = 'landing' | 'loading' | 'verdict' | 'out-of-scope' | 'error';
export function App() {
  const [state, setState] = useState<AppState>('landing');
  const [currentClaim, setCurrentClaim] = useState('');
  const [verdictData, setVerdictData] = useState(
    MOCK_VERDICTS["Nobody's hiring anymore"]
  );
  const handleCheckClaim = (claim: string) => {
    setCurrentClaim(claim);
    setState('loading');
  };
  const handleLoadingComplete = () => {
    if (currentClaim === OUT_OF_SCOPE_CLAIM) {
      setState('out-of-scope');
      return;
    }
    // Random error simulation (10% chance)
    if (Math.random() < 0.1) {
      setState('error');
      return;
    }
    // Find mock data or default to the first one
    const data =
    MOCK_VERDICTS[currentClaim] || MOCK_VERDICTS["Nobody's hiring anymore"];
    setVerdictData(data);
    setState('verdict');
  };
  const handleReset = () => {
    setState('landing');
    setCurrentClaim('');
  };
  const renderScreen = () => {
    switch (state) {
      case 'landing':
        return <LandingScreen onCheckClaim={handleCheckClaim} />;
      case 'loading':
        return (
          <LoadingScreen
            claim={currentClaim}
            onComplete={handleLoadingComplete} />);


      case 'verdict':
        return (
          <VerdictScreen
            claim={currentClaim}
            data={verdictData}
            onReset={handleReset} />);


      case 'out-of-scope':
        return (
          <OutOfScopeScreen
            onSelectClaim={handleCheckClaim}
            onReset={handleReset} />);


      case 'error':
        return (
          <ErrorScreen
            onRetry={() => setState('loading')}
            onSelectClaim={handleCheckClaim} />);


      default:
        return <LandingScreen onCheckClaim={handleCheckClaim} />;
    }
  };
  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/30">
      {renderScreen()}
    </div>);

}