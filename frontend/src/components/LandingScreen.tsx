import React, { useState } from 'react';
import { Header } from './Header';
import { ClaimChips } from './ClaimChips';
import { ArrowRight } from 'lucide-react';
interface LandingScreenProps {
  onCheckClaim: (claim: string) => void;
}
export function LandingScreen({ onCheckClaim }: LandingScreenProps) {
  const [inputValue, setInputValue] = useState('');
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onCheckClaim(inputValue);
    }
  };
  return (
    <div className="min-h-screen flex flex-col items-center px-4 pb-8 max-w-2xl mx-auto w-full">
      <Header />

      <main className="w-full flex flex-col items-center gap-8 flex-1">
        <p className="text-center text-muted-foreground text-sm font-sans max-w-xl">
          Built with multi-agent reasoning and MCP tools to query the MoSPI MCP server (India’s Ministry of Statistics and Programme Implementation).
        </p>
        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
          <div className="relative group">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="What did your uncle claim at dinner?"
              className="w-full bg-card border border-border rounded-xl p-6 text-lg md:text-xl font-serif placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all shadow-sm" />

          </div>

          <button
            type="submit"
            disabled={!inputValue.trim()}
            className="w-full bg-primary text-primary-foreground font-sans font-medium py-4 rounded-xl hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-primary/20">

            Check this claim
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="w-full pt-4">
          <p className="text-center text-muted-foreground text-sm mb-6 font-sans">
            Or try one of these common myths:
          </p>
          <ClaimChips onSelectClaim={onCheckClaim} />
        </div>
      </main>

      <footer className="mt-12 text-center space-y-2">
        <p className="text-xs text-muted-foreground font-sans">
          Powered by MoSPI eSankhyiki MCP
        </p>
        <a
          href="#"
          className="text-xs text-muted-foreground/60 hover:text-primary transition-colors font-sans block">

          Built by Rachitha Suresh
        </a>
      </footer>
    </div>);

}
