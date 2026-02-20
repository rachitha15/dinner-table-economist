import React, { useEffect, useState } from 'react';
import { Header } from './Header';
import { Check, Loader2 } from 'lucide-react';
interface LoadingScreenProps {
  claim: string;
  onComplete: () => void;
}
interface Step {
  id: number;
  label: string;
  duration: number;
  completedText: string;
}
const STEPS: Step[] = [
{
  id: 1,
  label: 'Discovering datasets...',
  duration: 700,
  completedText: 'Found 7 datasets → Selected PLFS'
},
{
  id: 2,
  label: 'Finding indicators...',
  duration: 1200,
  completedText: 'Matched 3 indicators for employment'
},
{
  id: 3,
  label: 'Preparing filters...',
  duration: 500,
  completedText: 'Filtered for 2020-2024, All India'
},
{
  id: 4,
  label: 'Fetching data...',
  duration: 1800,
  completedText: 'Retrieved 12 data points'
}];

export function LoadingScreen({ claim, onComplete }: LoadingScreenProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [interpreting, setInterpreting] = useState(false);
  useEffect(() => {
    let timeoutId: NodeJS.Timeout;
    const runSteps = async () => {
      for (let i = 0; i < STEPS.length; i++) {
        await new Promise((resolve) => {
          timeoutId = setTimeout(resolve, STEPS[i].duration);
        });
        setCurrentStep((prev) => prev + 1);
      }
      setInterpreting(true);
      timeoutId = setTimeout(() => {
        onComplete();
      }, 1500);
    };
    runSteps();
    return () => clearTimeout(timeoutId);
  }, [onComplete]);
  return (
    <div className="min-h-screen flex flex-col items-center px-4 pb-8 max-w-2xl mx-auto w-full">
      <Header compact />

      <div className="w-full mb-12">
        <div className="w-full bg-muted/30 border border-border rounded-xl p-4 text-lg font-serif text-muted-foreground italic">
          "{claim}"
        </div>
      </div>

      <div className="w-full max-w-md relative">
        {/* Vertical connecting line */}
        <div className="absolute left-[15px] top-4 bottom-4 w-[2px] bg-border z-0" />

        <div className="space-y-8 relative z-10">
          {STEPS.map((step) => {
            const isCompleted = currentStep > step.id;
            const isActive = currentStep === step.id;
            const isWaiting = currentStep < step.id;
            return (
              <div key={step.id} className="flex items-start gap-4">
                <div
                  className={`
                  w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 border-2 transition-all duration-300 bg-background
                  ${isCompleted ? 'border-green-500 text-green-500' : ''}
                  ${isActive ? 'border-primary text-primary' : ''}
                  ${isWaiting ? 'border-border text-muted-foreground' : ''}
                `}>

                  {isCompleted ?
                  <Check className="w-4 h-4" /> :
                  isActive ?
                  <Loader2 className="w-4 h-4 animate-spin" /> :

                  <span className="text-xs font-mono">{step.id}</span>
                  }
                </div>

                <div className="flex-1 pt-1">
                  <div className="flex items-center justify-between mb-1">
                    <p
                      className={`font-sans font-medium text-sm ${isWaiting ? 'text-muted-foreground' : 'text-foreground'}`}>

                      {isCompleted ? step.label.replace('...', '') : step.label}
                    </p>
                    {isCompleted &&
                    <span className="text-xs font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">
                        {(step.duration / 1000).toFixed(1)}s
                      </span>
                    }
                  </div>

                  <div
                    className={`overflow-hidden transition-all duration-500 ${isCompleted ? 'max-h-20 opacity-100' : 'max-h-0 opacity-0'}`}>

                    <p className="text-xs text-muted-foreground font-sans">
                      {step.completedText}
                    </p>
                  </div>
                </div>
              </div>);

          })}

          {/* Final Interpreting Step */}
          <div
            className={`flex items-start gap-4 transition-all duration-500 ${interpreting ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>

            <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 border-2 border-primary text-primary bg-background">
              <Loader2 className="w-4 h-4 animate-spin" />
            </div>
            <div className="pt-1">
              <p className="font-sans font-medium text-sm text-foreground">
                Interpreting results...
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>);

}