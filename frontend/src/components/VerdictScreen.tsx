import React, { useMemo, useState } from 'react';
import { Share2, ChevronDown, ChevronUp, ArrowLeft } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid } from
'recharts';
import { VerdictData } from '../utils/mockData';
import { BackstagePanel } from './BackstagePanel';
interface VerdictScreenProps {
  claim: string;
  data: VerdictData;
  onReset: () => void;
}
export function VerdictScreen({ claim, data, onReset }: VerdictScreenProps) {
  const [showBackstage, setShowBackstage] = useState(false);
  const metricLabel = data.chartData?.[0]?.label;
  const stagedSteps = useMemo(() => {
    const steps = data.mcpSteps || [];
    const source = data.source || '';
    const match = source.match(/^([A-Z]+)\s/);
    const datasetLabel = match ? match[1] : 'dataset';
    const step1 = steps.find((step) => step.id === 1);
    const step2 = steps.find((step) => step.id === 2);
    const step3 = steps.find((step) => step.id === 3);
    const step4 = steps.find((step) => step.id === 4);
    return [
      {
        id: 1,
        name: 'Classifier agent',
        description: 'Used MCP tool 1_know_about_mospi_api (cached) and selected a dataset.',
        result: `Selected ${datasetLabel}`,
        time: step1?.time || '',
        rawJson: step1?.rawJson || ''
      },
      {
        id: 2,
        name: 'Selector‑A agent',
        description: 'Used MCP tool 2_get_indicators to choose indicator parameters.',
        result: 'Indicators selected',
        time: step2?.time || '',
        rawJson: step2?.rawJson || ''
      },
      {
        id: 3,
        name: 'Selector‑B agent',
        description: 'Used MCP tool 3_get_metadata to choose filters.',
        result: 'Filters selected',
        time: step3?.time || '',
        rawJson: step3?.rawJson || ''
      },
      {
        id: 4,
        name: 'MCP fetch',
        description: 'Used MCP tool 4_get_data to retrieve data points.',
        result: 'Data points retrieved',
        time: step4?.time || '',
        rawJson: step4?.rawJson || ''
      },
      {
        id: 5,
        name: 'Interpreter agent',
        description: 'Interpreted the data points to produce the verdict.',
        result: 'Verdict generated',
        time: '',
        rawJson: ''
      }
    ];
  }, [data.mcpSteps, data.source]);
  const getVerdictStyles = (verdict: string) => {
    switch (verdict) {
      case 'busted':
        return 'bg-[#e8735a]/20 text-[#e8735a] border-[#e8735a]';
      case 'confirmed':
        return 'bg-green-500/20 text-green-400 border-green-500';
      case 'complicated':
        return 'bg-amber-500/20 text-amber-400 border-amber-500';
      default:
        return 'bg-muted text-muted-foreground border-border';
    }
  };
  return (
    <div className="min-h-screen flex flex-col items-center px-4 py-8 max-w-2xl mx-auto w-full">
      {/* Top Bar */}
      <div className="w-full flex justify-between items-start mb-8">
        <button
          onClick={onReset}
          className="text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Back">

          <ArrowLeft className="w-6 h-6" />
        </button>
        <button
          className="text-muted-foreground hover:text-primary transition-colors"
          aria-label="Share">

          <Share2 className="w-5 h-5" />
        </button>
      </div>

      {/* Content */}
      <main className="w-full flex flex-col gap-6">
        <h1 className="text-3xl md:text-4xl font-serif text-foreground leading-tight">
          "{claim}"
        </h1>

        <div
          className={`inline-flex self-start px-4 py-1.5 rounded-full border text-sm font-bold tracking-wider uppercase ${getVerdictStyles(data.verdict)}`}>

          {data.verdict.replace('-', ' ')}
        </div>

        <h2 className="text-2xl md:text-3xl font-sans font-bold text-foreground tracking-tight">
          {data.headlineStat}
        </h2>

        <p className="text-base md:text-lg text-muted-foreground leading-relaxed font-sans">
          {data.explanation}
        </p>

        {/* Chart */}
        <div className="w-full h-64 mt-4 bg-card/50 rounded-xl border border-border p-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.chartData}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#2a2a30"
                vertical={false} />

              <XAxis
                dataKey="year"
                stroke="#888"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                dy={10} />

              <YAxis
                stroke="#888"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                dx={-10} />

              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1a1f',
                  borderColor: '#2a2a30',
                  borderRadius: '8px',
                  color: '#f0f0f0'
                }}
                itemStyle={{
                  color: '#e8735a'
                }}
                formatter={(value: number) => [
                  value,
                  metricLabel || 'Value'
                ]} />

              <Line
                type="monotone"
                dataKey="value"
                stroke="#e8735a"
                strokeWidth={3}
                dot={{
                  fill: '#e8735a',
                  strokeWidth: 2,
                  r: 4
                }}
                activeDot={{
                  r: 6,
                  fill: '#fff'
                }} />

            </LineChart>
          </ResponsiveContainer>
        </div>
        {metricLabel && (
          <p className="text-xs text-muted-foreground font-sans mt-2">
            Metric: {metricLabel}
          </p>
        )}

        <p className="text-xs text-muted-foreground font-sans border-l-2 border-border pl-3 italic">
          Source: {data.source}
        </p>

        {/* Expandable Backstage */}
        <div className="mt-8 border-t border-border pt-6">
          <button
            onClick={() => setShowBackstage(!showBackstage)}
            className="w-full flex items-center justify-between p-4 bg-card rounded-lg border border-border hover:border-primary/50 transition-all group">

            <span className="font-medium text-foreground group-hover:text-primary transition-colors">
              How did AI get this data? (See MCP and Multi Agents in action)
            </span>
            {showBackstage ?
            <ChevronUp className="w-5 h-5 text-muted-foreground group-hover:text-primary" /> :

            <ChevronDown className="w-5 h-5 text-muted-foreground group-hover:text-primary" />
            }
          </button>

          {showBackstage && <BackstagePanel steps={stagedSteps} />}
        </div>

        <button
          onClick={onReset}
          className="w-full mt-8 py-4 rounded-xl border border-primary text-primary font-medium hover:bg-primary/10 transition-colors">

          Try another claim
        </button>
      </main>

      <footer className="mt-16 text-center">
        <p className="text-xs text-muted-foreground font-sans">
          The Dinner Table Economist • Built by Rachitha Suresh
        </p>
      </footer>
    </div>);

}
