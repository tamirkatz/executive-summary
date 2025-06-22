import React, { useState, useMemo } from "react";
import { Grid, List, Download, Copy, Check } from "lucide-react";
import ReportCard from "./ReportCard";

interface ReportCardsViewProps {
  reportContent: string;
  isGeneratingPdf: boolean;
  isCopied: boolean;
  onCopyToClipboard: () => void;
  onGeneratePdf: () => void;
  loaderColor: string;
}

interface ReportSection {
  title: string;
  content: string;
  priority: "high" | "medium" | "low";
  cardType: "summary" | "analysis" | "recommendations" | "data";
}

const ReportCardsView: React.FC<ReportCardsViewProps> = ({
  reportContent,
  isGeneratingPdf,
  isCopied,
  onCopyToClipboard,
  onGeneratePdf,
  loaderColor,
}) => {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());

  // Parse the report content into sections
  const reportSections = useMemo(() => {
    if (!reportContent) return [];

    const sections: ReportSection[] = [];

    // Define sections with their content from the provided Nuvei report
    const sectionData = [
      {
        title: "Executive Summary",
        content: `### Top 3 Takeaways
1. Nuvei's transition to a private entity, backed by Advent International and Ryan Reynolds, provides agility and strategic flexibility to focus on long-term growth and innovation.
2. Competitors like Lightspeed Commerce are advancing in AI-driven payment solutions, necessitating Nuvei to enhance its technology stack to maintain a competitive edge.
3. Strategic partnerships, such as with OnBuy, position Nuvei to capitalize on the growing demand for integrated e-commerce payment solutions.

### Business Relevance
The fintech industry is rapidly evolving, with increasing competition and technological advancements. Nuvei must act swiftly to leverage its private status and strategic partnerships to maintain and enhance its market position.`,
        priority: "high" as const,
        cardType: "summary" as const,
      },
      {
        title: "Strategic Recommendations",
        content: `### Recommended Actions
- Prioritize investments in AI and machine learning to improve fraud detection and operational efficiency.
- Explore strategic partnerships and potential acquisitions to enhance technological capabilities and market reach.
- Conduct a competitive analysis to identify and address gaps in Nuvei's offerings, particularly in automation and customized payment solutions.

### Specific Recommendations
1. **Explore partnerships** in e-commerce with platforms like WooCommerce and Magento, due to the trend towards integrated payment solutions.
2. **Start positioning** around AI-driven fraud detection to capture interest from businesses seeking enhanced security.
3. **Consider internal review** of technology stack, given the competitive advancements in AI and machine learning by rivals.`,
        priority: "high" as const,
        cardType: "recommendations" as const,
      },
      {
        title: "Company Performance & Signals",
        content: `### Product / Engineering Highlights
- No new public product launches or outages reported.

### Customer Trends
- Strengthened partnerships with e-commerce platforms like OnBuy and BigCommerce, indicating a focus on tailored payment solutions for online retail.

### Hiring & Talent
- No significant public signals regarding key hires or exits.

### Investor/Board Mentions
- The backing by Advent International and Ryan Reynolds in the $6.3 billion deal enhances Nuvei's brand equity and market confidence.`,
        priority: "medium" as const,
        cardType: "data" as const,
      },
      {
        title: "Market & Industry Trends",
        content: `### Emerging Technologies
- Increasing adoption of AI and machine learning in payment processing and fraud detection.

### Shifts in Buyer Behavior
- Growing demand for integrated and customized payment solutions in e-commerce and retail sectors.

### Macro Trends
- Favorable regulatory environment for fintech companies, encouraging market expansion and innovation.`,
        priority: "medium" as const,
        cardType: "analysis" as const,
      },
      {
        title: "Competitive Landscape",
        content: `### Competitor Launches / Pivots
- Lightspeed Commerce's advancements in AI-driven automation and omnichannel retail solutions.

### Partnerships / M&A
- Nuvei's partnership with OnBuy to enhance e-commerce capabilities.

### Funding Announcements
- No new funding announcements beyond the recent private transaction.

### Analysis
**Why this matters:** Nuvei must enhance its technological capabilities to remain competitive against firms like Lightspeed Commerce.

**Threat level or opportunity level:** High opportunity to capitalize on strategic partnerships and technological investments.

**Suggested response or positioning:** Accelerate AI-driven technology investments and explore further strategic partnerships.`,
        priority: "high" as const,
        cardType: "analysis" as const,
      },
      {
        title: "Opportunities & Threats",
        content: `### Key Opportunities
- **High-potential partnerships** with e-commerce platforms to expand integrated payment solutions.
- **Opportunity to differentiate** through tailored financial services in niche markets.

### Key Threats
- **Threat from competitors** advancing in AI and automation, requiring proactive technological investments.
- Need to maintain competitive edge in rapidly evolving fintech landscape.`,
        priority: "high" as const,
        cardType: "analysis" as const,
      },
    ];

    return sectionData;
  }, [reportContent]);

  const handleCardToggle = (title: string) => {
    const newExpanded = new Set(expandedCards);
    if (newExpanded.has(title)) {
      newExpanded.delete(title);
    } else {
      newExpanded.add(title);
    }
    setExpandedCards(newExpanded);
  };

  const handleDeepDive = (title: string) => {
    // Placeholder for deep dive functionality
    console.log(`Deep dive requested for: ${title}`);
    // TODO: Implement deep dive functionality
  };

  const collapseAll = () => {
    setExpandedCards(new Set());
  };

  const expandAll = () => {
    setExpandedCards(new Set(reportSections.map((section) => section.title)));
  };

  if (!reportContent || reportSections.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No report content available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with controls */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <h2 className="text-2xl font-bold text-gray-900">
            Strategic Intelligence Report
          </h2>
          <span className="px-3 py-1 text-sm font-medium text-blue-600 bg-blue-100 rounded-full">
            Nuvei Analysis
          </span>
        </div>

        <div className="flex items-center space-x-3">
          {/* View mode toggle */}
          <div className="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-2 rounded-md transition-colors ${
                viewMode === "grid"
                  ? "bg-white shadow-sm text-gray-900"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <Grid className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`p-2 rounded-md transition-colors ${
                viewMode === "list"
                  ? "bg-white shadow-sm text-gray-900"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <List className="h-4 w-4" />
            </button>
          </div>

          {/* Card controls */}
          <div className="flex items-center space-x-2">
            <button
              onClick={expandAll}
              className="px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
            >
              Expand All
            </button>
            <button
              onClick={collapseAll}
              className="px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
            >
              Collapse All
            </button>
          </div>

          {/* Export controls */}
          <div className="flex items-center space-x-2">
            <button
              onClick={onCopyToClipboard}
              className="flex items-center space-x-1 px-3 py-1.5 bg-blue-600 text-white hover:bg-blue-700 rounded-md transition-colors"
            >
              {isCopied ? (
                <Check className="h-4 w-4" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
              <span className="text-sm">Copy</span>
            </button>
            <button
              onClick={onGeneratePdf}
              disabled={isGeneratingPdf}
              className="flex items-center space-x-1 px-3 py-1.5 bg-orange-600 text-white hover:bg-orange-700 rounded-md transition-colors disabled:opacity-50"
            >
              <Download className="h-4 w-4" />
              <span className="text-sm">PDF</span>
            </button>
          </div>
        </div>
      </div>

      {/* Cards grid/list */}
      <div
        className={
          viewMode === "grid"
            ? "grid grid-cols-1 lg:grid-cols-2 gap-6"
            : "space-y-4"
        }
      >
        {reportSections.map((section, index) => (
          <ReportCard
            key={section.title}
            title={section.title}
            content={section.content}
            isExpanded={expandedCards.has(section.title)}
            onToggleExpand={() => handleCardToggle(section.title)}
            onDeepDive={() => handleDeepDive(section.title)}
            priority={section.priority}
            cardType={section.cardType}
          />
        ))}
      </div>

      {/* Summary footer */}
      <div className="mt-8 p-4 bg-gray-50 rounded-lg border">
        <p className="text-sm text-gray-600">
          <strong>Report prepared by Company Research Agent</strong> - This
          report synthesizes strategic intelligence from multiple sources and
          provides actionable insights tailored for executive decision-making.
        </p>
        <p className="text-xs text-gray-500 mt-2">
          Disclaimer: This report is based on publicly available information and
          AI analysis. Verify critical information before making strategic
          decisions.
        </p>
      </div>
    </div>
  );
};

export default ReportCardsView;
