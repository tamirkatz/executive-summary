import { useState, useEffect, useRef } from "react";
import Header from "./components/Header";
import ResearchBriefings from "./components/ResearchBriefings";
import CurationExtraction from "./components/CurationExtraction";
import ResearchQueries from "./components/ResearchQueries";
import ResearchStatus from "./components/ResearchStatus";
import ResearchReport from "./components/ResearchReport";
import ResearchForm from "./components/ResearchForm";
import ReportPreview from "./components/ReportPreview";
import {
  ResearchOutput,
  DocCount,
  DocCounts,
  EnrichmentCounts,
  ResearchState,
  ResearchStatusType,
} from "./types";
import { checkForFinalReport } from "./utils/handlers";
import {
  colorAnimation,
  dmSansStyle,
  glassStyle,
  fadeInAnimation,
} from "./styles";

const API_URL = import.meta.env.VITE_API_URL;
const WS_URL = import.meta.env.VITE_WS_URL;

if (!API_URL || !WS_URL) {
  throw new Error(
    "Environment variables VITE_API_URL and VITE_WS_URL must be set"
  );
}

// Add styles to document head
const colorStyle = document.createElement("style");
colorStyle.textContent = colorAnimation;
document.head.appendChild(colorStyle);

const dmSansStyleElement = document.createElement("style");
dmSansStyleElement.textContent = dmSansStyle;
document.head.appendChild(dmSansStyleElement);

function App() {
  // Check if we should show the preview mode
  const [showPreview, setShowPreview] = useState(() => {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get("preview") === "true";
  });

  const [isResearching, setIsResearching] = useState(false);
  const [status, setStatus] = useState<ResearchStatusType | null>(null);
  const [output, setOutput] = useState<ResearchOutput | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [hasFinalReport, setHasFinalReport] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const maxReconnectAttempts = 3;
  const reconnectDelay = 2000; // 2 seconds
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
  const [isEnrichmentExpanded, setIsEnrichmentExpanded] = useState(true);

  // Add state for phase tracking
  const [currentPhase, setCurrentPhase] = useState<
    "search" | "enrichment" | "briefing" | "complete" | null
  >(null);

  // Add new state for PDF generation
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const [, setPdfUrl] = useState<string | null>(null);

  const [isResetting, setIsResetting] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  // Add new state for color cycling
  const [loaderColor, setLoaderColor] = useState("#468BFF");

  // Add useEffect for color cycling
  useEffect(() => {
    if (!isResearching) return;

    const colors = [
      "#468BFF", // Blue
      "#8FBCFA", // Light Blue
      "#FE363B", // Red
      "#FF9A9D", // Light Red
      "#FDBB11", // Yellow
      "#F6D785", // Light Yellow
    ];

    let currentIndex = 0;

    const interval = setInterval(() => {
      currentIndex = (currentIndex + 1) % colors.length;
      setLoaderColor(colors[currentIndex]);
    }, 1000);

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
      setIsEnrichmentExpanded(true);
      setIsResetting(false);
      setHasScrolledToStatus(false); // Reset scroll flag when resetting research
    }, 300); // Match this with CSS transition duration
  };

  const connectWebSocket = (jobId: string) => {
    console.log("Initializing WebSocket connection for job:", jobId);

    // Use the WS_URL directly if it's a full URL, otherwise construct it
    const wsUrl =
      WS_URL.startsWith("wss://") || WS_URL.startsWith("ws://")
        ? `${WS_URL}/research/ws/${jobId}`
        : `${
            window.location.protocol === "https:" ? "wss:" : "ws:"
          }//${WS_URL}/research/ws/${jobId}`;

    console.log("Connecting to WebSocket URL:", wsUrl);

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("🔗 WebSocket connection established for job:", jobId);
      setReconnectAttempts(0);
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
              setIsEnrichmentExpanded(true);
            } else if (step === "Briefing" && currentPhase !== "briefing") {
              setCurrentPhase("briefing");
              setIsEnrichmentExpanded(false);
              setIsBriefingExpanded(true);
            }
          }

          // Handle completion
          if (statusData.status === "completed") {
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
                report: statusData.result?.report || "",
              },
            });
            setHasFinalReport(true);

            // Clear polling interval if it exists
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
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

            // Handle enrichment phase
            if (statusData.result.step === "Enriching") {
              console.log("📚 Enrichment phase updates");
              setIsEnrichmentExpanded(true);
              // Collapse enrichment section when complete
              if (statusData.status === "enrichment_complete") {
                setTimeout(() => {
                  setIsEnrichmentExpanded(false);
                }, 1000);
              }
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
    setReconnectAttempts(0);
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

  // Add new function to handle copying to clipboard
  const handleCopyToClipboard = async () => {
    if (!output?.details?.report) return;

    try {
      await navigator.clipboard.writeText(output.details.report);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000); // Reset after 2 seconds
    } catch (err) {
      console.error("Failed to copy text: ", err);
      setError("Failed to copy to clipboard");
    }
  };

  // Function to render progress components in order
  const renderProgressComponents = () => {
    console.log("🎨 Rendering progress components:", {
      hasOutput: !!output,
      currentPhase,
      shouldShowQueries,
      queriesCount: researchState.queries.length,
      streamingQueriesCount: Object.keys(researchState.streamingQueries).length,
      briefingStatus: {
        company: researchState.company,
        financial: researchState.financial,
        news: researchState.news,
      },
    });

    const components = [];

    // Research Report (always at the top when available)
    if (output && output.details) {
      console.log("📄 Rendering ResearchReport component");
      components.push(
        <ResearchReport
          key="report"
          output={{
            summary: output.summary,
            details: {
              report: output.details.report || "",
            },
          }}
          isResetting={isResetting}
          glassStyle={glassStyle}
          fadeInAnimation={fadeInAnimation}
          loaderColor={loaderColor}
          isGeneratingPdf={isGeneratingPdf}
          isCopied={isCopied}
          onCopyToClipboard={handleCopyToClipboard}
          onGeneratePdf={handleGeneratePdf}
        />
      );
    }

    // Current phase component
    if (
      currentPhase === "briefing" ||
      (currentPhase === "complete" &&
        researchState.company &&
        researchState.financial &&
        researchState.news)
    ) {
      console.log("📝 Rendering ResearchBriefings component");
      components.push(
        <ResearchBriefings
          key="briefing"
          briefingStatus={researchState}
          isExpanded={isBriefingExpanded}
          onToggleExpand={() => setIsBriefingExpanded(!isBriefingExpanded)}
          glassStyle={glassStyle.base}
        />
      );
    }

    if (
      currentPhase === "enrichment" ||
      currentPhase === "briefing" ||
      currentPhase === "complete"
    ) {
      console.log("📚 Rendering CurationExtraction component");
      components.push(
        <CurationExtraction
          key="enrichment"
          enrichmentCounts={researchState.enrichmentCounts}
          isExpanded={isEnrichmentExpanded}
          onToggleExpand={() => setIsEnrichmentExpanded(!isEnrichmentExpanded)}
          isResetting={isResetting}
          loaderColor={loaderColor}
        />
      );
    }

    // Queries are always at the bottom when visible
    if (
      shouldShowQueries &&
      (researchState.queries.length > 0 ||
        Object.keys(researchState.streamingQueries).length > 0)
    ) {
      console.log("🔍 Rendering ResearchQueries component");
      components.push(
        <ResearchQueries
          key="queries"
          queries={researchState.queries}
          streamingQueries={researchState.streamingQueries}
          isExpanded={isQueriesExpanded}
          onToggleExpand={() => setIsQueriesExpanded(!isQueriesExpanded)}
          isResetting={isResetting}
          glassStyle={glassStyle.base}
        />
      );
    }

    console.log("🎨 Total components to render:", components.length);
    return components;
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

  const togglePreview = () => {
    const newShowPreview = !showPreview;
    setShowPreview(newShowPreview);

    // Update URL without page reload
    const url = new URL(window.location.href);
    if (newShowPreview) {
      url.searchParams.set("preview", "true");
    } else {
      url.searchParams.delete("preview");
    }
    window.history.pushState(null, "", url);
  };

  // If preview mode is active, show the preview component
  if (showPreview) {
    return (
      <div className="relative">
        {/* Toggle button */}
        <div className="fixed top-4 right-4 z-50">
          <button
            onClick={togglePreview}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg shadow-lg hover:bg-blue-700 transition-colors"
          >
            ← Back to Main App
          </button>
        </div>
        <ReportPreview />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-white via-gray-50 to-white p-8 relative">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,rgba(70,139,255,0.35)_1px,transparent_0)] bg-[length:24px_24px] bg-center"></div>
      <div className="max-w-5xl mx-auto space-y-8 relative">
        {/* Toggle button */}
        <div className="absolute top-0 right-0 z-10">
          <button
            onClick={togglePreview}
            className="px-4 py-2 bg-green-600 text-white rounded-lg shadow-lg hover:bg-green-700 transition-colors"
          >
            🎯 Preview Cards UI
          </button>
        </div>

        {/* Header Component */}
        <Header glassStyle={glassStyle.card} />

        {/* Form Section */}
        <ResearchForm
          onSubmit={handleFormSubmit}
          isResearching={isResearching}
          glassStyle={glassStyle}
          loaderColor={loaderColor}
        />

        {/* Error Message */}
        {error && (
          <div
            className={`${
              glassStyle.card
            } border-[#FE363B]/30 bg-[#FE363B]/10 ${fadeInAnimation.fadeIn} ${
              isResetting
                ? "opacity-0 transform -translate-y-4"
                : "opacity-100 transform translate-y-0"
            } font-['DM_Sans']`}
          >
            <p className="text-[#FE363B]">{error}</p>
          </div>
        )}

        {/* Status Box */}
        <ResearchStatus
          status={status}
          error={error}
          isComplete={isComplete}
          currentPhase={currentPhase}
          isResetting={isResetting}
          glassStyle={glassStyle}
          loaderColor={loaderColor}
          statusRef={statusRef}
        />

        {/* Progress Components Container */}
        <div className="space-y-12 transition-all duration-500 ease-in-out">
          {renderProgressComponents()}
        </div>
      </div>
    </div>
  );
}

export default App;
