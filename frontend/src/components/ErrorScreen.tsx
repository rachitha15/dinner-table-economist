import React from 'react';
import { Header } from './Header';
import { ClaimChips } from './ClaimChips';
import { AlertCircle, RefreshCw } from 'lucide-react';
interface ErrorScreenProps {
  onRetry: () => void;
  onSelectClaim: (claim: string) => void;
}
export function ErrorScreen({ onRetry, onSelectClaim }: ErrorScreenProps) {
  return (
    <div className="min-h-screen flex flex-col items-center px-4 pb-8 max-w-2xl mx-auto w-full">
      <Header compact />

      <main className="w-full flex flex-col items-center gap-8 flex-1 pt-8">
        <div className="bg-destructive/10 border border-destructive/20 rounded-xl p-8 text-center w-full">
          <div className="w-12 h-12 bg-destructive/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-6 h-6 text-destructive" />
          </div>
          <h2 className="text-xl font-serif text-foreground mb-2">
            The government data server isn't responding right now
          </h2>
          <p className="text-muted-foreground mb-6">
            This sometimes happens — it's a beta service.
          </p>

          <button
            onClick={onRetry}
            className="bg-primary text-primary-foreground px-6 py-2 rounded-lg font-medium hover:bg-primary/90 transition-colors flex items-center gap-2 mx-auto">

            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
        </div>

        <div className="w-full">
          <p className="text-center text-muted-foreground text-sm mb-6">
            Or try a different claim:
          </p>
          <ClaimChips onSelectClaim={onSelectClaim} />
        </div>
      </main>
    </div>);

}