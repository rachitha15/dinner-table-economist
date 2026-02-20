import React from 'react';
import { Header } from './Header';
import { ClaimChips } from './ClaimChips';
import { Info, ArrowLeft } from 'lucide-react';
interface OutOfScopeScreenProps {
  onSelectClaim: (claim: string) => void;
  onReset: () => void;
}
export function OutOfScopeScreen({
  onSelectClaim,
  onReset
}: OutOfScopeScreenProps) {
  return (
    <div className="min-h-screen flex flex-col items-center px-4 pb-8 max-w-2xl mx-auto w-full">
      <Header compact />

      <main className="w-full flex flex-col items-center gap-8 flex-1 pt-8">
        <div className="bg-card border border-border rounded-xl p-8 text-center w-full">
          <div className="w-12 h-12 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
            <Info className="w-6 h-6 text-muted-foreground" />
          </div>
          <h2 className="text-xl font-serif text-foreground mb-2">
            This claim can't be fact-checked with available economic data
          </h2>

          <div className="my-6 text-left bg-muted/30 rounded-lg p-4">
            <p className="text-sm font-medium text-foreground mb-2">
              The MoSPI MCP covers:
            </p>
            <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
              <li>Employment & Labour Statistics</li>
              <li>Inflation (CPI & WPI)</li>
              <li>GDP & National Accounts</li>
              <li>Industrial Output (IIP)</li>
              <li>Energy Statistics</li>
              <li>Environment Statistics</li>
            </ul>
          </div>

          <p className="text-sm text-muted-foreground mb-6">
            Try one of these instead:
          </p>
          <ClaimChips onSelectClaim={onSelectClaim} />
        </div>

        <button
          onClick={onReset}
          className="text-primary hover:text-primary/80 font-medium flex items-center gap-2 transition-colors">

          <ArrowLeft className="w-4 h-4" />
          Ask something else
        </button>
      </main>
    </div>);

}