import React from 'react';
interface HeaderProps {
  compact?: boolean;
}
export function Header({ compact = false }: HeaderProps) {
  return (
    <header
      className={`w-full flex flex-col items-center justify-center text-center px-4 ${compact ? 'pt-8 pb-6' : 'pt-20 pb-12'}`}>

      <h1
        className={`${compact ? 'text-2xl' : 'text-3xl md:text-4xl'} font-serif text-foreground mb-2 tracking-tight`}>

        The Dinner Table Economist
      </h1>
      <p className="text-muted-foreground font-sans text-sm md:text-base max-w-md">
        Fact-check dinner table economics with real government data
      </p>
    </header>);

}