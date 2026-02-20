import React, { useEffect, useState } from 'react';
import { LandingScreen } from './components/LandingScreen';
import { LoadingScreen } from './components/LoadingScreen';
import { VerdictScreen } from './components/VerdictScreen';
import { OutOfScopeScreen } from './components/OutOfScopeScreen';
import { ErrorScreen } from './components/ErrorScreen';
import type { VerdictData } from './utils/mockData';
type AppState = 'landing' | 'loading' | 'verdict' | 'out-of-scope' | 'error';
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
export function App() {
  const [state, setState] = useState<AppState>('landing');
  const [currentClaim, setCurrentClaim] = useState('');
  const [verdictData, setVerdictData] = useState<VerdictData | null>(null);
  const [requestId, setRequestId] = useState(0);
  const [datasetLabel, setDatasetLabel] = useState<string | null>(null);
  const [apiDone, setApiDone] = useState(false);
  const [loadingDone, setLoadingDone] = useState(false);
  const handleCheckClaim = (claim: string) => {
    setCurrentClaim(claim);
    setState('loading');
    setDatasetLabel(null);
    setApiDone(false);
    setLoadingDone(false);
    setRequestId((prev) => prev + 1);
  };
  useEffect(() => {
    if (state !== 'loading' || !currentClaim) {
      return;
    }
    const controller = new AbortController();
    const run = async () => {
      try {
        const response = await fetch(`${API_URL}/api/check-claim`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ claim: currentClaim }),
          signal: controller.signal
        });
        const data = await response.json();
        if (!response.ok) {
          setState('error');
          return;
        }
        if (data?.outOfScope) {
          setState('out-of-scope');
          return;
        }
        const source = typeof data?.source === 'string' ? data.source : '';
        const match = source.match(/^([A-Z]+)\s/);
        const label = match ? match[1] : null;
        setDatasetLabel(label);
        setVerdictData(data);
        setApiDone(true);
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }
        setState('error');
      }
    };
    run();
    return () => controller.abort();
  }, [state, currentClaim, requestId]);
  useEffect(() => {
    if (state === 'loading' && apiDone && loadingDone) {
      setState('verdict');
    }
  }, [state, apiDone, loadingDone]);
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
            datasetLabel={datasetLabel}
            onComplete={() => setLoadingDone(true)} />);


      case 'verdict':
        if (!verdictData) {
          return (
            <ErrorScreen
              onRetry={() => setState('loading')}
              onSelectClaim={handleCheckClaim} />);
        }
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
