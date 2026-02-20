import React, { useState } from 'react';
import { Check, ChevronDown, ChevronUp } from 'lucide-react';
import { MCPStep } from '../utils/mockData';
interface BackstagePanelProps {
  steps: MCPStep[];
}
export function BackstagePanel({ steps }: BackstagePanelProps) {
  return (
    <div className="w-full mt-8 animate-accordion-down">
      <div className="mb-6">
        <h3 className="text-xl font-serif text-foreground mb-2">
          MCP in action — 4 steps to real data
        </h3>
        <p className="text-sm text-muted-foreground font-sans">
          MCP (Model Context Protocol) lets AI connect to external data sources.
          Here's exactly what happened:
        </p>
      </div>

      <div className="relative pl-4">
        {/* Dotted connecting line */}
        <div className="absolute left-[23px] top-4 bottom-12 w-[2px] border-l-2 border-dotted border-border" />

        <div className="space-y-6">
          {steps.map((step) =>
          <StepCard key={step.id} step={step} />
          )}
        </div>
      </div>
    </div>);

}
function StepCard({ step }: {step: MCPStep;}) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="relative pl-8">
      {/* Connector dot */}
      <div className="absolute left-0 top-6 w-2 h-2 rounded-full bg-border -translate-x-[1px]" />

      <div className="bg-card border border-border rounded-lg p-4 transition-all hover:border-primary/30">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="bg-primary/10 text-primary text-xs font-bold px-2 py-0.5 rounded uppercase tracking-wider">
              Step {step.id}
            </span>
            <span className="font-serif text-foreground">{step.name}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
              {step.time}
            </span>
            <Check className="w-4 h-4 text-green-500" />
          </div>
        </div>

        <p className="text-sm text-foreground font-medium mb-1">
          {step.description}
        </p>
        <p className="text-sm text-muted-foreground mb-3">{step.result}</p>

        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors font-medium">

          {expanded ? 'Hide raw response' : 'See raw response'}
          {expanded ?
          <ChevronUp className="w-3 h-3" /> :

          <ChevronDown className="w-3 h-3" />
          }
        </button>

        {expanded &&
        <div className="mt-3 bg-black/50 rounded p-3 overflow-x-auto">
            <pre className="text-xs font-mono text-muted-foreground leading-relaxed">
              {step.rawJson}
            </pre>
          </div>
        }
      </div>
    </div>);

}