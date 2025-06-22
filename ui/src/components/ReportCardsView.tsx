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

  // Parse the actual report content into sections
  const reportSections = useMemo(() => {
    if (!reportContent) return [];

    const sections: ReportSection[] = [];

    // Split the report by main headers (# headers)
    const mainSections = reportContent
      .split(/(?=^# )/gm)
      .filter((section) => section.trim());

    // Extract company name from the report title if available
    const titleMatch = reportContent.match(/Executive Strategic Brief: (.+)/);
    const companyName = titleMatch ? titleMatch[1] : "Company";

    for (const section of mainSections) {
      const lines = section.trim().split("\n");
      if (lines.length === 0) continue;

      // Extract the main header
      const headerLine = lines.find((line) => line.startsWith("# "));
      if (!headerLine) continue;

      const title = headerLine.replace("# ", "").trim();

      // Skip the main document title
      if (
        title.includes("Executive Strategic Brief") ||
        title.includes("Research Report")
      ) {
        continue;
      }

      // Get the content (everything after the header)
      const contentStartIndex =
        lines.findIndex((line) => line.startsWith("# ")) + 1;
      const content = lines.slice(contentStartIndex).join("\n").trim();

      if (!content) continue;

      // Determine card type and priority based on section title
      const { cardType, priority } = determineCardTypeAndPriority(title);

      sections.push({
        title,
        content,
        cardType,
        priority,
      });
    }

    return sections;
  }, [reportContent]);

  // Helper function to determine card type and priority based on section title
  const determineCardTypeAndPriority = (
    title: string
  ): {
    cardType: ReportSection["cardType"];
    priority: ReportSection["priority"];
  } => {
    const lowerTitle = title.toLowerCase();

    // Market-centric section mapping
    if (
      lowerTitle.includes("market intelligence") ||
      lowerTitle.includes("highlights")
    ) {
      return { cardType: "analysis", priority: "high" };
    }
    if (lowerTitle.includes("ecosystem") || lowerTitle.includes("technology")) {
      return { cardType: "analysis", priority: "medium" };
    }
    if (
      lowerTitle.includes("competitor") ||
      lowerTitle.includes("launches") ||
      lowerTitle.includes("moves")
    ) {
      return { cardType: "analysis", priority: "high" };
    }
    if (lowerTitle.includes("regulatory") || lowerTitle.includes("changes")) {
      return { cardType: "data", priority: "medium" };
    }
    if (
      lowerTitle.includes("company fit") ||
      lowerTitle.includes("gaps") ||
      lowerTitle.includes("positioning")
    ) {
      return { cardType: "analysis", priority: "high" };
    }
    if (
      lowerTitle.includes("strategic recommendations") ||
      lowerTitle.includes("recommendations")
    ) {
      return { cardType: "recommendations", priority: "high" };
    }

    // Legacy section mapping for backward compatibility
    if (
      lowerTitle.includes("executive summary") ||
      lowerTitle.includes("summary")
    ) {
      return { cardType: "summary", priority: "high" };
    }
    if (lowerTitle.includes("performance") || lowerTitle.includes("signals")) {
      return { cardType: "data", priority: "medium" };
    }
    if (
      lowerTitle.includes("market") ||
      lowerTitle.includes("trends") ||
      lowerTitle.includes("industry")
    ) {
      return { cardType: "analysis", priority: "medium" };
    }
    if (
      lowerTitle.includes("opportunities") ||
      lowerTitle.includes("threats")
    ) {
      return { cardType: "analysis", priority: "high" };
    }

    // Default fallback
    return { cardType: "analysis", priority: "medium" };
  };

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

  // Extract company name for display
  const titleMatch = reportContent.match(/Executive Strategic Brief: (.+)/);
  const companyName = titleMatch ? titleMatch[1] : "Company";

  return (
    <div className="space-y-6">
      {/* Header with controls */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <h2 className="text-2xl font-bold text-gray-900">
            Strategic Intelligence Report
          </h2>
          <span className="px-3 py-1 text-sm font-medium text-blue-600 bg-blue-100 rounded-full">
            {companyName} Analysis
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
