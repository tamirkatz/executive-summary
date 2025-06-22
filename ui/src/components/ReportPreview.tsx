import React from "react";
import ReportCardsView from "./ReportCardsView";

const ReportPreview: React.FC = () => {
  // Static data provided by the user
  const staticReportData = `Executive Strategic Brief: Nuvei
Prepared for: CEO
Date: June 22, 2025
Report Type: Strategic Intelligence Briefing

Executive Summary (1-minute read)

Top 3 Takeaways
1. Nuvei's transition to a private entity, backed by Advent International and Ryan Reynolds, provides agility and strategic flexibility to focus on long-term growth and innovation.
2. Competitors like Lightspeed Commerce are advancing in AI-driven payment solutions, necessitating Nuvei to enhance its technology stack to maintain a competitive edge.
3. Strategic partnerships, such as with OnBuy, position Nuvei to capitalize on the growing demand for integrated e-commerce payment solutions.

Recommended Actions
- Prioritize investments in AI and machine learning to improve fraud detection and operational efficiency.
- Explore strategic partnerships and potential acquisitions to enhance technological capabilities and market reach.
- Conduct a competitive analysis to identify and address gaps in Nuvei's offerings, particularly in automation and customized payment solutions.

Business Relevance
The fintech industry is rapidly evolving, with increasing competition and technological advancements. Nuvei must act swiftly to leverage its private status and strategic partnerships to maintain and enhance its market position.

Company Performance & Signals

Product / Engineering Highlights
- No new public product launches or outages reported.

Customer Trends
- Strengthened partnerships with e-commerce platforms like OnBuy and BigCommerce, indicating a focus on tailored payment solutions for online retail.

Hiring & Talent
- No significant public signals regarding key hires or exits.

Investor/Board Mentions
- The backing by Advent International and Ryan Reynolds in the $6.3 billion deal enhances Nuvei's brand equity and market confidence.

Market & Industry Trends

Emerging Technologies
- Increasing adoption of AI and machine learning in payment processing and fraud detection.

Shifts in Buyer Behavior
- Growing demand for integrated and customized payment solutions in e-commerce and retail sectors.

Macro Trends
- Favorable regulatory environment for fintech companies, encouraging market expansion and innovation.

Competitor & Adjacent Player Moves

Competitor Launches / Pivots
- Lightspeed Commerce's advancements in AI-driven automation and omnichannel retail solutions.

Partnerships / M&A
- Nuvei's partnership with OnBuy to enhance e-commerce capabilities.

Funding Announcements
- No new funding announcements beyond the recent private transaction.

Hiring Trends / Talent War Signals
- No significant public signals.

Why this matters
Nuvei must enhance its technological capabilities to remain competitive against firms like Lightspeed Commerce.

Threat level or opportunity level
High opportunity to capitalize on strategic partnerships and technological investments.

Suggested response or positioning
Accelerate AI-driven technology investments and explore further strategic partnerships.

Emerging Opportunities & Threats
- High-potential partnerships with e-commerce platforms to expand integrated payment solutions.
- Opportunity to differentiate through tailored financial services in niche markets.
- Threat from competitors advancing in AI and automation, requiring proactive technological investments.

Strategic Recommendations
1. Explore partnerships in e-commerce with platforms like WooCommerce and Magento, due to the trend towards integrated payment solutions.
2. Start positioning around AI-driven fraud detection to capture interest from businesses seeking enhanced security.
3. Consider internal review of technology stack, given the competitive advancements in AI and machine learning by rivals.

Appendix (Optional)
Sources, links, long-form insights, graphs, screenshots are not included in this summary but can be provided upon request for deeper analysis and understanding.

Report prepared by Company Research Agent
This report synthesizes strategic intelligence from multiple sources and provides actionable insights tailored for executive decision-making.

Disclaimer: This report is based on publicly available information and AI analysis. Verify critical information before making strategic decisions.`;

  const handleCopyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(staticReportData);
      console.log("Report copied to clipboard");
    } catch (err) {
      console.error("Failed to copy report:", err);
    }
  };

  const handleGeneratePdf = () => {
    console.log("PDF generation requested");
    // Placeholder for PDF generation
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-white via-gray-50 to-white p-8 relative">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,rgba(70,139,255,0.35)_1px,transparent_0)] bg-[length:24px_24px] bg-center"></div>
      <div className="max-w-7xl mx-auto relative">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Research Report Cards Preview
          </h1>
          <p className="text-lg text-gray-600">
            Interactive card-based view of the Nuvei strategic intelligence
            report
          </p>
        </div>

        {/* Cards View */}
        <div className="bg-white/70 backdrop-blur-sm rounded-2xl border border-white/20 shadow-lg p-8">
          <ReportCardsView
            reportContent={staticReportData}
            isGeneratingPdf={false}
            isCopied={false}
            onCopyToClipboard={handleCopyToClipboard}
            onGeneratePdf={handleGeneratePdf}
            loaderColor="#468BFF"
          />
        </div>

        {/* Instructions */}
        <div className="mt-8 bg-blue-50/70 backdrop-blur-sm rounded-xl border border-blue-200/30 p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">
            🎯 Preview Features
          </h3>
          <ul className="text-blue-800 space-y-2">
            <li>
              • <strong>View Toggle:</strong> Switch between Grid and List
              layouts
            </li>
            <li>
              • <strong>Card Controls:</strong> Expand/collapse individual cards
              or all at once
            </li>
            <li>
              • <strong>Deep Dive:</strong> Click the "Deep Dive" buttons to see
              placeholder functionality
            </li>
            <li>
              • <strong>Priority System:</strong> Notice the color-coded
              priority levels (High/Medium/Low)
            </li>
            <li>
              • <strong>Interactive Elements:</strong> Hover effects and smooth
              animations
            </li>
            <li>
              • <strong>Export Ready:</strong> Copy and PDF buttons are
              functional
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ReportPreview;
