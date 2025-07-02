import { useState, useEffect, useRef } from "react";
import Header from "./components/Header";
import ResearchStatus from "./components/ResearchStatus";
import EnhancedResearchReport from "./components/EnhancedResearchReport";
import { askQuestionAboutCard } from "./utils/chatApi";
import ResearchForm from "./components/ResearchForm";
import CompetitorReview from "./components/CompetitorReview";
import {
  ResearchOutput,
  DocCount,
  DocCounts,
  EnrichmentCounts,
  ResearchState,
  ResearchStatusType,
  Competitor,
} from "./types";
import { checkForFinalReport } from "./utils/handlers";

// Enhanced styling with modern gradients and effects
const modernColorAnimation = `
@keyframes modernColorFlow {
  0% { stroke: #2563eb; }
  20% { stroke: #4f46e5; }
  40% { stroke: #7c3aed; }
  60% { stroke: #6366f1; }
  80% { stroke: #3b82f6; }
  100% { stroke: #2563eb; }
}

@keyframes subtleFloat {
  0%, 100% { 
    transform: translateY(0px);
    opacity: 0.8;
  }
  50% { 
    transform: translateY(-10px);
    opacity: 1;
  }
}

@keyframes shimmer {
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
}

.animate-modern-colors {
  animation: modernColorFlow 6s ease-in-out infinite;
}

.animate-float {
  animation: subtleFloat 4s ease-in-out infinite;
}

.shimmer {
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0) 0%,
    rgba(255, 255, 255, 0.1) 50%,
    rgba(255, 255, 255, 0) 100%
  );
  background-size: 1000px 100%;
  animation: shimmer 3s infinite linear;
}

.loader-icon {
  transition: stroke 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Modern glass morphism */
.glass-modern {
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
}

.glass-card-modern {
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 
    0 20px 25px -5px rgba(0, 0, 0, 0.1),
    0 10px 10px -5px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
}
`;

const dmSansStyle = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700;9..40,800&family=Inter:wght@300;400;500;600;700;800&display=swap');
  
  body {
    font-family: 'Inter', 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  }
`;

// Enhanced glass styles
const enhancedGlassStyle = {
  base: "glass-modern",
  card: "glass-card-modern rounded-2xl p-8 hover:shadow-lg transition-shadow duration-300",
  input:
    "bg-white/95 border border-gray-100 shadow-sm pl-12 w-full rounded-xl py-3 px-4 text-gray-900 focus:border-blue-400/50 focus:outline-none focus:ring-2 focus:ring-blue-400/30 placeholder-gray-500 transition-all duration-300",
};

const fadeInAnimation = {
  fadeIn: "transition-all duration-500 ease-out transform",
  writing: "animate-pulse",
  colorTransition: modernColorAnimation,
};

// Resolve backend endpoints from env vars first, then fall back to the current
// page origin/host so the same build works in dev (localhost) and prod.
const API_URL =
  (import.meta.env.VITE_API_URL as string) || window.location.origin;

// WebSocket host (protocol is added later in buildWsUrl).
const WS_URL = (import.meta.env.VITE_WS_URL as string) || window.location.host;

// Optional sanity-check – warn (don't crash) if not explicitly set
if (!import.meta.env.VITE_API_URL || !import.meta.env.VITE_WS_URL) {
  console.warn(
    "VITE_API_URL / VITE_WS_URL not provided – falling back to current origin"
  );
}

// Add enhanced styles to document head
const colorStyle = document.createElement("style");
colorStyle.textContent = modernColorAnimation;
document.head.appendChild(colorStyle);

const dmSansStyleElement = document.createElement("style");
dmSansStyleElement.textContent = dmSansStyle;
document.head.appendChild(dmSansStyleElement);

function App() {
  const [isResearching, setIsResearching] = useState(false);
  const [status, setStatus] = useState<ResearchStatusType | null>(null);
  const [output, setOutput] = useState<ResearchOutput | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [hasFinalReport, setHasFinalReport] = useState(false);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const [researchState, setResearchState] = useState<ResearchState>({
    company: false,
    financial: false,
    news: false,
    streamingQueries: {},
    queries: [],
  });
  const [originalCompanyName, setOriginalCompanyName] = useState<string>("");

  // Add ref for status section
  const statusRef = useRef<HTMLDivElement>(null);

  // Add state to track initial scroll
  const [hasScrolledToStatus, setHasScrolledToStatus] = useState(false);

  // Modify the scroll helper function
  const scrollToStatus = () => {
    if (!hasScrolledToStatus && statusRef.current) {
      const yOffset = -20; // Reduced negative offset to scroll further down
      const y =
        statusRef.current.getBoundingClientRect().top +
        window.pageYOffset +
        yOffset;
      window.scrollTo({ top: y, behavior: "smooth" });
      setHasScrolledToStatus(true);
    }
  };

  // Add new state for query section collapse
  const [isQueriesExpanded, setIsQueriesExpanded] = useState(true);
  const [shouldShowQueries, setShouldShowQueries] = useState(false);

  // Add new state for tracking search phase
  const [isSearchPhase, setIsSearchPhase] = useState(false);

  // Add state for section collapse
  const [isBriefingExpanded, setIsBriefingExpanded] = useState(true);

  // Add state for phase tracking
  const [currentPhase, setCurrentPhase] = useState<
    | "search"
    | "enrichment"
    | "briefing"
    | "competitor_review"
    | "complete"
    | null
  >(null);

  // Add competitor review state
  const [showCompetitorReview, setShowCompetitorReview] = useState(false);
  const [discoveredCompetitors, setDiscoveredCompetitors] = useState<
    Competitor[]
  >([]);
  const [currentJobId, setCurrentJobId] = useState<string>("");

  // Add new state for PDF generation
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const [, setPdfUrl] = useState<string | null>(null);

  const [isResetting, setIsResetting] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  // Enhanced color cycling with modern palette
  const [loaderColor, setLoaderColor] = useState("#6366f1");

  // Add useEffect for modern color cycling
  useEffect(() => {
    if (!isResearching) return;

    const modernColors = [
      "#6366f1", // Indigo
      "#8b5cf6", // Violet
      "#ec4899", // Pink
      "#f59e0b", // Amber
      "#10b981", // Emerald
      "#3b82f6", // Blue
    ];

    let currentIndex = 0;

    const interval = setInterval(() => {
      currentIndex = (currentIndex + 1) % modernColors.length;
      setLoaderColor(modernColors[currentIndex]);
    }, 1200);

    return () => clearInterval(interval);
  }, [isResearching]);

  const resetResearch = () => {
    setIsResetting(true);

    // Use setTimeout to create a smooth transition
    setTimeout(() => {
      setStatus(null);
      setOutput(null);
      setError(null);
      setIsComplete(false);
      setResearchState({
        company: false,
        financial: false,
        news: false,
        streamingQueries: {},
        queries: [],
      });
      setPdfUrl(null);
      setCurrentPhase(null);
      setIsSearchPhase(false);
      setShouldShowQueries(false);
      setIsQueriesExpanded(true);
      setIsBriefingExpanded(true);
      setIsResetting(false);
      setHasScrolledToStatus(false); // Reset scroll flag when resetting research
      setShowCompetitorReview(false);
      setDiscoveredCompetitors([]);
      setCurrentJobId("");
    }, 400); // Slightly longer for smoother transitions
  };

  const handleCompetitorConfirm = async (modifiedCompetitors: Competitor[]) => {
    try {
      console.log(
        "🔄 Submitting competitor modifications and starting Phase 2"
      );
      setStatus({
        step: "Starting Phase 2",
        message: `Continuing research with ${modifiedCompetitors.length} selected competitors...`,
      });

      const response = await fetch(`${API_URL}/research/competitors/modify`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          job_id: currentJobId,
          competitors: modifiedCompetitors,
        }),
      });

      if (response.ok) {
        setShowCompetitorReview(false);
        setCurrentPhase("enrichment");
        setIsResearching(true); // Ensure research state is active
        setIsComplete(false); // Ensure not marked as complete
        console.log("✅ Competitors confirmed, Phase 2 starting...");
      } else {
        throw new Error("Failed to confirm competitors");
      }
    } catch (error) {
      console.error("❌ Error confirming competitors:", error);
      setError("Failed to confirm competitors. Please try again.");
    }
  };

  const handleCompetitorCancel = () => {
    console.log("❌ User cancelled competitor selection");
    setShowCompetitorReview(false);
    setCurrentPhase(null);
    setIsResearching(false);
  };

  const connectWebSocket = (jobId: string) => {
    console.log("Initializing WebSocket connection for job:", jobId);

    // Helper to build a WebSocket URL that always matches the security context
    const buildWsUrl = (baseUrl: string, jobId: string) => {
      // Strip any leading protocol so we can safely prepend the correct one
      const host = baseUrl.replace(/^(https?:\/\/|wss?:\/\/)/, "");
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      return `${protocol}//${host}/research/ws/${jobId}`;
    };

    const wsUrl = buildWsUrl(WS_URL, jobId);

    console.log("Connecting to WebSocket URL:", wsUrl);

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("🔗 WebSocket connection established for job:", jobId);
    };

    ws.onclose = (event) => {
      console.log("🔌 WebSocket disconnected", {
        jobId,
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean,
        timestamp: new Date().toISOString(),
      });

      if (isResearching && !hasFinalReport) {
        console.log(
          "🔄 Starting polling for final report due to WebSocket disconnection"
        );
        // Start polling for final report
        if (!pollingIntervalRef.current) {
          pollingIntervalRef.current = setInterval(
            () =>
              checkForFinalReport(
                jobId,
                setOutput,
                setStatus,
                setIsComplete,
                setIsResearching,
                setCurrentPhase,
                setHasFinalReport,
                pollingIntervalRef
              ),
            5000
          );
        }
      }
    };

    ws.onerror = (error) => {
      console.error("❌ WebSocket error:", error);
    };

    ws.onmessage = (event) => {
      try {
        console.log("🔍 WebSocket message received:", event.data);
        const rawData = JSON.parse(event.data);

        if (rawData.type === "status_update") {
          const statusData = rawData.data;
          console.log("📊 Status update received:", {
            status: statusData.status,
            message: statusData.message,
            result: statusData.result,
            timestamp: rawData.timestamp,
          });

          // Add defensive checks for required fields
          if (!statusData || typeof statusData !== "object") {
            console.warn("❌ Invalid status data received:", statusData);
            return;
          }

          // Handle competitor review required
          if (statusData.status === "competitor_review_required") {
            console.log("🏆 Competitor review required");
            const competitors = statusData.result?.competitors || [];
            setDiscoveredCompetitors(competitors);
            setShowCompetitorReview(true);
            setCurrentPhase("competitor_review");
            // Keep isResearching true during competitor review
            setIsResearching(true);
            setIsComplete(false);
            setStatus({
              step: "Competitor Review",
              message:
                statusData.message ||
                "Please review the discovered competitors",
            });
          }

          // Handle competitor review completion
          if (statusData.status === "competitor_review_completed") {
            console.log("✅ Competitor review completed");
            setShowCompetitorReview(false);
            setCurrentPhase("enrichment");
          }

          // Handle Phase 2 start (analysis after competitor review)
          if (
            statusData.status === "processing" &&
            statusData.result?.step === "Phase 2"
          ) {
            console.log(
              "🔄 Phase 2 (Analysis) starting with modified competitors"
            );
            setIsComplete(false);
            setIsResearching(true);
            setCurrentPhase("enrichment");
            setShowCompetitorReview(false);
            setStatus({
              step: "Phase 2: Analysis",
              message:
                statusData.message ||
                "Continuing research with selected competitors",
            });
          }

          // Handle phase transitions
          if (statusData.result?.step) {
            const step = statusData.result.step;
            console.log("🔄 Phase transition:", {
              from: currentPhase,
              to: step,
            });
            if (step === "Search" && currentPhase !== "search") {
              setCurrentPhase("search");
              setIsSearchPhase(true);
              setShouldShowQueries(true);
              setIsQueriesExpanded(true);
            } else if (step === "Enriching" && currentPhase !== "enrichment") {
              setCurrentPhase("enrichment");
              setIsSearchPhase(false);
              setIsQueriesExpanded(false);
            } else if (step === "Briefing" && currentPhase !== "briefing") {
              setCurrentPhase("briefing");
              setIsBriefingExpanded(true);
            } else if (step === "Competitor Review") {
              setCurrentPhase("competitor_review");
            }
          }

          // Handle discovery completion (Phase 1 only)
          if (statusData.status === "discovery_complete") {
            console.log(
              "✅ Discovery phase completed - waiting for competitor review"
            );
            // Don't set isComplete or isResearching to false - just update status
            setStatus({
              step: "Discovery Complete",
              message:
                statusData.message ||
                "Discovery completed - waiting for user review",
            });
          }

          // Handle completion – only mark flow complete when a report is present
          if (statusData.status === "completed") {
            if (!statusData.result?.report) {
              // Intermediate component-level completion – ignore
              console.log(
                "⚠️ Received 'completed' status without report – treating as intermediate step"
              );
            } else {
              console.log("✅ Research completed successfully");
              setCurrentPhase("complete");
              setIsComplete(true);
              setIsResearching(false);
              setStatus({
                step: "Complete",
                message: "Research completed successfully",
              });
              setOutput({
                summary: "",
                details: {
                  report: statusData.result.report,
                },
              });
              setHasFinalReport(true);

              // Clear polling interval if it exists
              if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
                pollingIntervalRef.current = null;
              }
            }
          }

          // Set search phase when first query starts generating
          if (statusData.status === "query_generating" && !isSearchPhase) {
            console.log("🔍 Starting search phase");
            setIsSearchPhase(true);
            setShouldShowQueries(true);
            setIsQueriesExpanded(true);
          }

          // End search phase and start enrichment when moving to next step
          if (statusData.result?.step && statusData.result.step !== "Search") {
            if (isSearchPhase) {
              console.log("🔄 Ending search phase, starting enrichment");
              setIsSearchPhase(false);
              // Add delay before collapsing queries
              setTimeout(() => {
                setIsQueriesExpanded(false);
              }, 1000);
            }

            // Handle briefing phase
            if (statusData.result.step === "Briefing") {
              console.log("📝 Briefing phase updates");
              setIsBriefingExpanded(true);
              if (
                statusData.status === "briefing_complete" &&
                statusData.result?.category
              ) {
                // Update briefing status
                console.log(
                  "✅ Briefing completed for category:",
                  statusData.result.category
                );
                setResearchState((prev) => ({
                  ...prev,
                  company: true,
                  financial: true,
                  news: true,
                }));
              }
            }
          }

          // Handle enrichment-specific updates
          if (statusData.result?.step === "Enriching") {
            console.log("📚 Enrichment update:", {
              status: statusData.status,
              category: statusData.result.category,
              count: statusData.result.count,
              total: statusData.result.total,
              enriched: statusData.result.enriched,
            });

            // Initialize enrichment counts when starting a category
            if (statusData.status === "category_start") {
              const category = statusData.result
                .category as keyof EnrichmentCounts;
              if (category) {
                console.log("🚀 Starting enrichment for category:", category);
                setResearchState((prev) => ({
                  ...prev,
                  enrichmentCounts: {
                    ...prev.enrichmentCounts,
                    [category]: {
                      total: statusData.result.count || 0,
                      enriched: 0,
                    },
                  } as EnrichmentCounts,
                }));
              }
            }
            // Update enriched count when a document is processed
            else if (statusData.status === "document_enriched") {
              const category = statusData.result
                .category as keyof EnrichmentCounts;
              if (category) {
                console.log("📄 Document enriched for category:", category);
                setResearchState((prev) => {
                  const currentCounts = prev.enrichmentCounts?.[category];
                  if (currentCounts) {
                    return {
                      ...prev,
                      enrichmentCounts: {
                        ...prev.enrichmentCounts,
                        [category]: {
                          ...currentCounts,
                          enriched: Math.min(
                            currentCounts.enriched + 1,
                            currentCounts.total
                          ),
                        },
                      } as EnrichmentCounts,
                    };
                  }
                  return prev;
                });
              }
            }
            // Handle extraction errors
            else if (statusData.status === "extraction_error") {
              const category = statusData.result
                .category as keyof EnrichmentCounts;
              console.log("❌ Extraction error for category:", category);
              if (category) {
                setResearchState((prev) => {
                  const currentCounts = prev.enrichmentCounts?.[category];
                  if (currentCounts) {
                    return {
                      ...prev,
                      enrichmentCounts: {
                        ...prev.enrichmentCounts,
                        [category]: {
                          ...currentCounts,
                          total: Math.max(0, currentCounts.total - 1),
                        },
                      } as EnrichmentCounts,
                    };
                  }
                  return prev;
                });
              }
            }
            // Update final counts when a category is complete
            else if (statusData.status === "category_complete") {
              const category = statusData.result
                .category as keyof EnrichmentCounts;
              console.log("✅ Category complete:", category, {
                total: statusData.result.total,
                enriched: statusData.result.enriched,
              });
              if (category) {
                setResearchState((prev) => ({
                  ...prev,
                  enrichmentCounts: {
                    ...prev.enrichmentCounts,
                    [category]: {
                      total: statusData.result.total || 0,
                      enriched: statusData.result.enriched || 0,
                    },
                  } as EnrichmentCounts,
                }));
              }
            }
          }

          // Handle curation-specific updates
          if (statusData.result?.step === "Curation") {
            console.log("📋 Curation update:", {
              status: statusData.status,
              doc_type: statusData.result.doc_type,
              doc_counts: statusData.result.doc_counts,
            });

            // Initialize doc counts when curation starts
            if (
              statusData.status === "processing" &&
              statusData.result.doc_counts
            ) {
              console.log(
                "🚀 Starting curation with doc counts:",
                statusData.result.doc_counts
              );
              setResearchState((prev) => ({
                ...prev,
                docCounts: statusData.result.doc_counts as DocCounts,
              }));
            }
            // Update initial count for a category
            else if (statusData.status === "category_start") {
              const docType = statusData.result?.doc_type as keyof DocCounts;
              if (docType) {
                console.log("📁 Starting curation for doc type:", docType);
                setResearchState((prev) => ({
                  ...prev,
                  docCounts: {
                    ...prev.docCounts,
                    [docType]: {
                      initial: statusData.result.initial_count,
                      kept: 0,
                    } as DocCount,
                  } as DocCounts,
                }));
              }
            }
            // Increment the kept count for a specific category
            else if (statusData.status === "document_kept") {
              const docType = statusData.result?.doc_type as keyof DocCounts;
              console.log("✅ Document kept for type:", docType);
              setResearchState((prev) => {
                if (docType && prev.docCounts?.[docType]) {
                  return {
                    ...prev,
                    docCounts: {
                      ...prev.docCounts,
                      [docType]: {
                        initial: prev.docCounts[docType].initial,
                        kept: prev.docCounts[docType].kept + 1,
                      },
                    } as DocCounts,
                  };
                }
                return prev;
              });
            }
            // Update final doc counts when curation is complete
            else if (
              statusData.status === "curation_complete" &&
              statusData.result.doc_counts
            ) {
              console.log(
                "✅ Curation complete with final counts:",
                statusData.result.doc_counts
              );
              setResearchState((prev) => ({
                ...prev,
                docCounts: statusData.result.doc_counts as DocCounts,
              }));
            }
          }

          // Handle briefing status updates
          if (statusData.status === "briefing_start") {
            console.log("📝 Briefing started:", statusData.message);
            setStatus({
              step: "Briefing",
              message: statusData.message,
            });
          } else if (
            statusData.status === "briefing_complete" &&
            statusData.result?.category
          ) {
            const category = statusData.result.category;
            console.log("✅ Briefing completed for category:", category);
            setResearchState((prev) => ({
              ...prev,
              company: true,
              financial: true,
              news: true,
            }));
          }

          // Handle query updates with defensive checks
          if (statusData.status === "query_generating") {
            console.log("🔍 Query generating:", {
              category: statusData.result?.category,
              query_number: statusData.result?.query_number,
              query: statusData.result?.query,
            });

            // Add defensive checks for required fields
            if (
              statusData.result?.category &&
              statusData.result?.query_number &&
              statusData.result?.query
            ) {
              setResearchState((prev) => {
                const key = `${statusData.result.category}-${statusData.result.query_number}`;
                console.log("📝 Updating streaming query with key:", key);
                return {
                  ...prev,
                  streamingQueries: {
                    ...prev.streamingQueries,
                    [key]: {
                      text: statusData.result.query,
                      number: statusData.result.query_number,
                      category: statusData.result.category,
                      isComplete: false,
                    },
                  },
                };
              });
            } else {
              console.warn(
                "Missing required fields in query_generating message:",
                statusData.result
              );
            }
          } else if (statusData.status === "query_generated") {
            console.log("✅ Query generated:", {
              category: statusData.result?.category,
              query_number: statusData.result?.query_number,
              query: statusData.result?.query,
            });

            // Add defensive checks for required fields
            if (
              statusData.result?.category &&
              statusData.result?.query_number &&
              statusData.result?.query
            ) {
              setResearchState((prev) => {
                // Remove from streaming queries and add to completed queries
                const key = `${statusData.result.category}-${statusData.result.query_number}`;
                console.log(
                  "🔄 Moving query from streaming to completed with key:",
                  key
                );
                const { [key]: _, ...remainingStreamingQueries } =
                  prev.streamingQueries;

                return {
                  ...prev,
                  streamingQueries: remainingStreamingQueries,
                  queries: [
                    ...prev.queries,
                    {
                      text: statusData.result.query,
                      number: statusData.result.query_number,
                      category: statusData.result.category,
                    },
                  ],
                };
              });
            } else {
              console.warn(
                "Missing required fields in query_generated message:",
                statusData.result
              );
            }
          }
          // Handle report streaming
          else if (statusData.status === "report_chunk") {
            console.log(
              "📄 Report chunk received, length:",
              statusData.result?.chunk?.length
            );
            if (statusData.result?.chunk) {
              setOutput((prev) => ({
                summary: "Generating report...",
                details: {
                  report: prev?.details?.report
                    ? prev.details.report + statusData.result.chunk
                    : statusData.result.chunk,
                },
              }));
            }
          }
          // Handle other status updates
          else if (statusData.status === "processing") {
            console.log("⚙️ Processing update:", {
              step: statusData.result?.step,
              message: statusData.message,
            });

            setIsComplete(false);
            // Only update status.step if we're not in curation or the new step is curation
            if (
              !status?.step ||
              status.step !== "Curation" ||
              statusData.result?.step === "Curation"
            ) {
              setStatus({
                step: statusData.result?.step || "Processing",
                message: statusData.message || "Processing...",
              });
            }

            // Reset briefing status when starting a new research
            if (statusData.result?.step === "Briefing") {
              console.log("🔄 Resetting briefing status for new research");
              setResearchState((prev) => ({
                ...prev,
                company: false,
                financial: false,
                news: false,
              }));
            }

            scrollToStatus();
          } else if (
            statusData.status === "failed" ||
            statusData.status === "error" ||
            statusData.status === "website_error"
          ) {
            console.error("❌ Research error:", {
              status: statusData.status,
              error: statusData.error,
              message: statusData.message,
            });

            setError(
              statusData.error || statusData.message || "Research failed"
            );
            if (
              statusData.status === "website_error" &&
              statusData.result?.continue_research
            ) {
            } else {
              setIsResearching(false);
              setIsComplete(false);
            }
          }
        }
      } catch (error) {
        console.error(
          "Error processing WebSocket message:",
          error,
          "Raw data:",
          event.data
        );
      }
    };

    wsRef.current = ws;
  };

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Create a custom handler for the form that receives form data
  const handleFormSubmit = async (formData: {
    companyName: string;
    companyUrl: string;
    userRole: string;
  }) => {
    console.log("🚀 Starting research for:", formData.companyName);

    // Clear any existing errors first
    setError(null);

    // If research is complete, reset the UI first
    if (isComplete) {
      console.log("🔄 Resetting UI for new research");
      resetResearch();
      await new Promise((resolve) => setTimeout(resolve, 300)); // Wait for reset animation
    }

    // Reset states
    setHasFinalReport(false);
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    setIsResearching(true);
    setOriginalCompanyName(formData.companyName);
    setHasScrolledToStatus(false); // Reset scroll flag when starting new research

    try {
      const url = `${API_URL}/research`;

      // Format the company URL if provided
      const formattedCompanyUrl = formData.companyUrl
        ? formData.companyUrl.startsWith("http://") ||
          formData.companyUrl.startsWith("https://")
          ? formData.companyUrl
          : `https://${formData.companyUrl}`
        : undefined;

      // Log the request details
      const requestData = {
        company: formData.companyName,
        company_url: formattedCompanyUrl,
        user_role: formData.userRole || undefined,
      };

      console.log("📤 Sending research request:", requestData);

      const response = await fetch(url, {
        method: "POST",
        mode: "cors",
        credentials: "omit",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      }).catch((error) => {
        console.error("❌ Fetch error:", error);
        throw error;
      });

      console.log("📥 Response received:", {
        status: response.status,
        ok: response.ok,
        statusText: response.statusText,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.log("❌ Error response:", errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("✅ Response data:", data);

      if (data.job_id) {
        console.log("🔗 Connecting WebSocket with job_id:", data.job_id);
        setCurrentJobId(data.job_id);
        connectWebSocket(data.job_id);
      } else {
        throw new Error("No job ID received");
      }
    } catch (err) {
      console.log("❌ Caught error:", err);
      setError(err instanceof Error ? err.message : "Failed to start research");
      setIsResearching(false);
    }
  };

  // Add new function to handle PDF generation
  const handleGeneratePdf = async () => {
    if (!output || isGeneratingPdf) return;

    setIsGeneratingPdf(true);
    try {
      console.log("Generating PDF with company name:", originalCompanyName);
      const response = await fetch(`${API_URL}/generate-pdf`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          report_content: output.details.report,
          company_name: originalCompanyName || output.details.report,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to generate PDF");
      }

      // Get the blob from the response
      const blob = await response.blob();

      // Create a URL for the blob
      const url = window.URL.createObjectURL(blob);

      // Create a temporary link element
      const link = document.createElement("a");
      link.href = url;
      link.download = `${originalCompanyName || "research_report"}.pdf`;

      // Append to body, click, and remove
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Clean up the URL
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error generating PDF:", error);
      setError(
        error instanceof Error ? error.message : "Failed to generate PDF"
      );
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  // Add cleanup for polling interval
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  // Add useEffect to log state changes
  useEffect(() => {
    console.log("🔄 Research state updated:", {
      isResearching,
      currentPhase,
      isSearchPhase,
      shouldShowQueries,
      researchState: {
        company: researchState.company,
        financial: researchState.financial,
        news: researchState.news,
        queriesCount: researchState.queries.length,
        streamingQueriesCount: Object.keys(researchState.streamingQueries)
          .length,
        enrichmentCounts: researchState.enrichmentCounts,
        docCounts: researchState.docCounts,
      },
    });
  }, [
    isResearching,
    currentPhase,
    isSearchPhase,
    shouldShowQueries,
    researchState,
  ]);

  // Add useEffect to log output changes
  useEffect(() => {
    if (output) {
      console.log("📄 Output updated:", {
        summary: output.summary,
        reportLength: output.details?.report?.length || 0,
      });
    }
  }, [output]);

  // Add useEffect to log status changes
  useEffect(() => {
    if (status) {
      console.log("📊 Status updated:", status);
    }
  }, [status]);

  // Handler to copy the generated report to the clipboard
  const handleCopyToClipboard = async () => {
    if (output?.details?.report) {
      try {
        await navigator.clipboard.writeText(output.details.report);
        setIsCopied(true);
        // Reset the copied state after a short delay for user feedback
        setTimeout(() => setIsCopied(false), 2000);
      } catch (err) {
        console.error("❌ Failed to copy report to clipboard:", err);
        setError("Failed to copy report to clipboard");
      }
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-b from-slate-50 to-white">
      {/* Modern Abstract Background */}
      <div className="absolute inset-0">
        {/* Subtle grid pattern */}
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, rgba(37, 99, 235, 0.05) 1px, transparent 0)`,
            backgroundSize: "40px 40px",
          }}
        ></div>

        {/* Soft gradient shapes */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden">
          <div className="absolute -top-1/2 -left-1/4 w-full h-full bg-blue-50/40 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-1/2 -right-1/4 w-full h-full bg-indigo-50/40 rounded-full blur-3xl"></div>
          <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-violet-50/30 rounded-full blur-2xl"></div>
        </div>
      </div>

      {/* Main content */}
      <div className="relative z-10 px-6 py-12 lg:px-8 lg:py-16">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <Header />

          {/* Enhanced Form Section */}
          <div className="mt-16">
            <div className={`${enhancedGlassStyle.card} max-w-4xl mx-auto`}>
              <ResearchForm
                onSubmit={handleFormSubmit}
                isResearching={isResearching}
                glassStyle={enhancedGlassStyle}
                loaderColor={loaderColor}
              />
            </div>
          </div>

          {/* Enhanced Error Message */}
          {error && (
            <div className="mt-8 max-w-4xl mx-auto">
              <div
                className={`${enhancedGlassStyle.card} border-red-100 bg-red-50/80`}
              >
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                  <p className="text-red-700 font-medium">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Status Box */}
          <div className="mt-8 max-w-4xl mx-auto">
            <ResearchStatus
              status={status}
              error={error}
              isComplete={isComplete}
              currentPhase={currentPhase}
              isResetting={isResetting}
              glassStyle={enhancedGlassStyle}
              loaderColor={loaderColor}
              statusRef={statusRef}
            />
          </div>

          {/* Competitor Review Modal */}
          <CompetitorReview
            competitors={discoveredCompetitors}
            onConfirm={handleCompetitorConfirm}
            onCancel={handleCompetitorCancel}
            isVisible={showCompetitorReview}
            glassStyle={enhancedGlassStyle}
          />

          {/* Final Research Report */}
          {output?.details?.report && (
            <div className="mt-12 max-w-7xl mx-auto">
              <EnhancedResearchReport
                output={output as ResearchOutput}
                isResetting={isResetting}
                glassStyle={enhancedGlassStyle}
                fadeInAnimation={fadeInAnimation}
                loaderColor={loaderColor}
                isGeneratingPdf={isGeneratingPdf}
                isCopied={isCopied}
                onCopyToClipboard={handleCopyToClipboard}
                onGeneratePdf={handleGeneratePdf}
                onAskQuestion={askQuestionAboutCard}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
