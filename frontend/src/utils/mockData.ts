export interface ChartDataPoint {
  year: string;
  value: number;
}

export interface MCPStep {
  id: number;
  name: string;
  description: string;
  result: string;
  time: string;
  rawJson: string;
}

export interface VerdictData {
  verdict: 'busted' | 'confirmed' | 'complicated';
  headlineStat: string;
  explanation: string;
  chartData: ChartDataPoint[];
  source: string;
  mcpSteps: MCPStep[];
}

export const MOCK_CLAIMS = [
'Inflation is out of control',
'Manufacturing is dead in India',
"India's economy is slowing down",
'Only services sector is growing',
'Wholesale prices are rising',
'Industrial production is growing',
'Factory output is increasing',
'Energy consumption is rising',
'Rural India has it worse than cities',
'Youth unemployment is a crisis',
'Women are leaving the workforce'];


export const MOCK_VERDICTS: Record<string, VerdictData> = {
  "Nobody's hiring anymore": {
    verdict: 'busted',
    headlineStat: 'Unemployment dropped from 4.2% to 3.2% since 2021',
    explanation:
    "According to the Periodic Labour Force Survey (PLFS) 2024, India's unemployment rate has steadily declined over the last three years. While specific sectors may face hiring freezes, the aggregate data shows a positive trend in overall employment.",
    chartData: [
    { year: '2020', value: 4.8 },
    { year: '2021', value: 4.2 },
    { year: '2022', value: 3.6 },
    { year: '2023', value: 3.4 },
    { year: '2024', value: 3.2 }],

    source:
    'Periodic Labour Force Survey 2024, Ministry of Statistics, Govt. of India',
    mcpSteps: [
    {
      id: 1,
      name: 'Discover',
      description: 'Asked MoSPI what datasets are available',
      result: '7 datasets found → Selected PLFS (jobs & employment)',
      time: '0.71s',
      rawJson:
      '{\n  "query": "employment datasets",\n  "found": 7,\n  "selected": "PLFS_Annual_2024",\n  "confidence": 0.98\n}'
    },
    {
      id: 2,
      name: 'Indicators',
      description: 'Finding relevant indicators',
      result: 'Matched 3 indicators for employment',
      time: '1.2s',
      rawJson:
      '{\n  "indicators": [\n    "unemployment_rate_urban",\n    "unemployment_rate_rural",\n    "lfpr_overall"\n  ]\n}'
    },
    {
      id: 3,
      name: 'Filters',
      description: 'Preparing filters',
      result: 'Filtered for 2020-2024, All India',
      time: '0.5s',
      rawJson:
      '{\n  "filters": {\n    "years": ["2020", "2021", "2022", "2023", "2024"],\n    "region": "All India",\n    "age_group": "15-29"\n  }\n}'
    },
    {
      id: 4,
      name: 'Fetch',
      description: 'Fetching data',
      result: 'Retrieved 12 data points',
      time: '1.8s',
      rawJson:
      '{\n  "status": "success",\n  "data_points": 12,\n  "source": "MoSPI API v2"\n}'
    }]

  },
  'Inflation is out of control': {
    verdict: 'complicated',
    headlineStat: 'CPI is 5.1%, down from peak but food inflation persists',
    explanation:
    'While headline inflation has moderated significantly from its 2022 peaks, food inflation remains volatile. The Consumer Price Index (CPI) shows overall stability, but specific categories like vegetables and pulses have seen double-digit growth.',
    chartData: [
    { year: '2020', value: 6.2 },
    { year: '2021', value: 5.5 },
    { year: '2022', value: 6.7 },
    { year: '2023', value: 5.4 },
    { year: '2024', value: 5.1 }],

    source: 'CPI Data 2024, Ministry of Statistics & Programme Implementation',
    mcpSteps: [
    {
      id: 1,
      name: 'Discover',
      description: 'Asked MoSPI for inflation data',
      result: 'Found CPI and WPI datasets',
      time: '0.65s',
      rawJson:
      '{\n  "query": "inflation",\n  "datasets": ["CPI_Combined", "WPI_All_Commodities"]\n}'
    },
    {
      id: 2,
      name: 'Indicators',
      description: 'Selecting inflation metrics',
      result: 'Selected CPI General Index',
      time: '0.9s',
      rawJson:
      '{\n  "indicator": "CPI_General_Index",\n  "base_year": 2012\n}'
    },
    {
      id: 3,
      name: 'Filters',
      description: 'Applying time range',
      result: 'Last 5 years, monthly average',
      time: '0.4s',
      rawJson: '{\n  "range": "2020-2024",\n  "frequency": "annual_avg"\n}'
    },
    {
      id: 4,
      name: 'Fetch',
      description: 'Retrieving indices',
      result: 'Data retrieved successfully',
      time: '1.5s',
      rawJson: '{\n  "status": "200 OK",\n  "records": 60\n}'
    }]

  },
  "India's economy is slowing down": {
    verdict: 'busted',
    headlineStat: 'GDP growth remains robust at 7.2% in FY24',
    explanation:
    "Contrary to the claim of slowing down, India's GDP growth has accelerated. The National Statistical Office (NSO) data indicates strong performance in manufacturing and construction sectors, outpacing global averages.",
    chartData: [
    { year: '2020', value: -5.8 },
    { year: '2021', value: 9.1 },
    { year: '2022', value: 7.0 },
    { year: '2023', value: 7.2 },
    { year: '2024', value: 7.2 }],

    source: 'Provisional Estimates of Annual National Income 2023-24, NSO',
    mcpSteps: [
    {
      id: 1,
      name: 'Discover',
      description: 'Searching National Accounts',
      result: 'Identified GDP at Constant Prices',
      time: '0.8s',
      rawJson: '{\n  "search": "GDP growth",\n  "dataset": "NAS_GVA_GDP"\n}'
    },
    {
      id: 2,
      name: 'Indicators',
      description: 'Isolating growth rates',
      result: 'YoY Growth Rate selected',
      time: '1.1s',
      rawJson: '{\n  "metric": "YoY_Growth_Percent",\n  "sector": "Total"\n}'
    },
    {
      id: 3,
      name: 'Filters',
      description: 'Setting timeframe',
      result: 'FY2020 to FY2024',
      time: '0.3s',
      rawJson: '{\n  "period": "FY20-FY24"\n}'
    },
    {
      id: 4,
      name: 'Fetch',
      description: 'Getting official estimates',
      result: '5 years of data fetched',
      time: '1.6s',
      rawJson: '{\n  "data_length": 5,\n  "unit": "Percent"\n}'
    }]

  },
  'Women are leaving the workforce': {
    verdict: 'confirmed',
    headlineStat: 'Female LFPR is low but showing recent recovery',
    explanation:
    'While there has been a long-term decline, recent PLFS data shows a slight uptick in Female Labour Force Participation Rate (LFPR), primarily in rural self-employment. However, compared to global standards, participation remains critically low.',
    chartData: [
    { year: '2020', value: 24.5 },
    { year: '2021', value: 25.1 },
    { year: '2022', value: 32.8 },
    { year: '2023', value: 37.0 },
    { year: '2024', value: 37.0 }],

    source: 'Periodic Labour Force Survey, Annual Report 2023-24',
    mcpSteps: [
    {
      id: 1,
      name: 'Discover',
      description: 'Querying gender statistics',
      result: 'Found PLFS Gender Disaggregated Data',
      time: '0.75s',
      rawJson: '{\n  "topic": "gender_employment",\n  "source": "PLFS"\n}'
    },
    {
      id: 2,
      name: 'Indicators',
      description: 'Selecting LFPR',
      result: 'Female LFPR (Urban + Rural)',
      time: '1.0s',
      rawJson: '{\n  "indicator": "LFPR_Female_All_Ages"\n}'
    },
    {
      id: 3,
      name: 'Filters',
      description: 'Time series analysis',
      result: '2020-2024 Trend',
      time: '0.6s',
      rawJson: '{\n  "type": "trend_analysis"\n}'
    },
    {
      id: 4,
      name: 'Fetch',
      description: 'Downloading tables',
      result: 'Data points extracted',
      time: '1.9s',
      rawJson: '{\n  "status": "complete"\n}'
    }]

  }
};

export const OUT_OF_SCOPE_CLAIM = "India doesn't care about environment";
