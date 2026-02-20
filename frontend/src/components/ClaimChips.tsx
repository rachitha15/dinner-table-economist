import React from 'react';
import { MOCK_CLAIMS } from '../utils/mockData';
interface ClaimChipsProps {
  onSelectClaim: (claim: string) => void;
  disabled?: boolean;
}
export function ClaimChips({
  onSelectClaim,
  disabled = false
}: ClaimChipsProps) {
  return (
    <div className="flex flex-wrap justify-center gap-3 w-full max-w-3xl mx-auto">
      {MOCK_CLAIMS.map((claim) =>
      <button
        key={claim}
        onClick={() => onSelectClaim(claim)}
        disabled={disabled}
        className={`
            px-4 py-2 rounded-full border text-sm font-sans transition-all duration-200
            ${disabled ? 'border-border text-muted-foreground opacity-50 cursor-not-allowed' : 'border-[#2a2a30] text-muted-foreground hover:border-primary hover:text-primary hover:bg-primary/5 active:scale-95'}
          `}>

          {claim}
        </button>
      )}
    </div>);

}