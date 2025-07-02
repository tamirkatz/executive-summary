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
  glassStyle: GlassStyle;
};

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface ResearchCardData {
  id: string;
  title: string;
  summary: string;
  content: string;
  chatHistory: ChatMessage[];
}

export interface ResearchCardProps {
  data: ResearchCardData;
  onAskQuestion?: (
    cardId: string,
    question: string,
    cardContent: string
  ) => Promise<string>;
  onRemove?: (cardId: string) => void;
  className?: string;
  initialWidth?: number;
  initialHeight?: number;
  minWidth?: number;
  minHeight?: number;
}

export interface ChatInputProps {
  onSubmit: (message: string) => Promise<void>;
  disabled?: boolean;
}

export interface ChatHistoryProps {
  messages: ChatMessage[];
  className?: string;
}

export type ViewMode = "report" | "cards";

export interface ReportPoint {
  id: string;
  title: string;
  content: string;
  category?: string;
}

export interface ViewToggleProps {
  currentView: ViewMode;
  onViewChange: (view: ViewMode) => void;
  className?: string;
}
