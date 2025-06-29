export type ResearchStatusType = {
  step: string;
  message: string;
};

export type ResearchOutput = {
  summary: string;
  details: {
    report: string;
  };
};

export type DocCount = {
  initial: number;
  kept: number;
};

export type DocCounts = {
  [key: string]: DocCount;
};

export type EnrichmentCounts = {
  company: { total: number; enriched: number };
  financial: { total: number; enriched: number };
  news: { total: number; enriched: number };
};

export type ResearchState = {
  company: boolean;
  financial: boolean;
  news: boolean;
  enrichmentCounts?: EnrichmentCounts;
  docCounts?: DocCounts;
  streamingQueries: {
    [key: string]: {
      text: string;
      number: number;
      category: string;
      isComplete: boolean;
    };
  };
  queries: Array<{
    text: string;
    number: number;
    category: string;
  }>;
};

export type GlassStyle = {
  base: string;
  card: string;
  input: string;
};

export type AnimationStyle = {
  fadeIn: string;
  writing: string;
  colorTransition: string;
};

export type Competitor = {
  name: string;
  description?: string;
  category?: string;
  confidence?: number;
  evidence?: string;
  website?: string;
};

export type ResearchStatusProps = {
  status: ResearchStatusType | null;
  error: string | null;
  isComplete: boolean;
  currentPhase:
    | "search"
    | "enrichment"
    | "briefing"
    | "competitor_review"
    | "complete"
    | null;
  isResetting: boolean;
  glassStyle: GlassStyle;
  loaderColor: string;
  statusRef: React.RefObject<HTMLDivElement>;
};

export type ResearchQueriesProps = {
  queries: Array<{
    text: string;
    number: number;
    category: string;
  }>;
  streamingQueries: {
    [key: string]: {
      text: string;
      number: number;
      category: string;
      isComplete: boolean;
    };
  };
  isExpanded: boolean;
  onToggleExpand: () => void;
  isResetting: boolean;
  glassStyle: string;
};
