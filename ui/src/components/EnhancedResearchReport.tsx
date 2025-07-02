import { useState, useEffect } from "react";
import {
  ResearchOutput,
  ViewMode,
  ResearchCardData,
  ChatMessage,
  GlassStyle,
} from "../types";
import ViewToggle from "./ViewToggle";
import ResearchCardGrid from "./ResearchCardGrid";
import ResearchReport from "./ResearchReport";
import { parseReportToCards, addMessageToCard } from "../utils/reportParser";

interface EnhancedResearchReportProps {
  output: ResearchOutput;
  isResetting: boolean;
  glassStyle: GlassStyle;
  fadeInAnimation: any;
  loaderColor: string;
  isGeneratingPdf: boolean;
  isCopied: boolean;
  onCopyToClipboard: () => void;
  onGeneratePdf: () => void;
  onAskQuestion?: (
    cardId: string,
    question: string,
    cardContent: string
  ) => Promise<string>;
}

const EnhancedResearchReport: React.FC<EnhancedResearchReportProps> = ({
  output,
  isResetting,
  glassStyle,
  fadeInAnimation,
  loaderColor,
  isGeneratingPdf,
  isCopied,
  onCopyToClipboard,
  onGeneratePdf,
  onAskQuestion,
}) => {
  const [currentView, setCurrentView] = useState<ViewMode>("report");
  const [cards, setCards] = useState<ResearchCardData[]>([]);

  // Parse report into cards when output changes
  useEffect(() => {
    if (output?.details?.report) {
      const parsedCards = parseReportToCards(output.details.report);
      setCards(parsedCards);
    }
  }, [output?.details?.report]);

  // Handle card removal
  const handleRemoveCard = (cardId: string) => {
    setCards((prevCards) => prevCards.filter((card) => card.id !== cardId));
  };

  // Default question handler if none provided
  const handleAskQuestion = async (
    cardId: string,
    question: string,
    cardContent: string
  ): Promise<string> => {
    if (onAskQuestion) {
      try {
        const response = await onAskQuestion(cardId, question, cardContent);

        // Add user message
        const userMessage: ChatMessage = {
          role: "user",
          content: question,
          timestamp: new Date().toISOString(),
        };

        // Add assistant response
        const assistantMessage: ChatMessage = {
          role: "assistant",
          content: response,
          timestamp: new Date().toISOString(),
        };

        setCards((prevCards) => {
          let updatedCards = addMessageToCard(prevCards, cardId, userMessage);
          updatedCards = addMessageToCard(
            updatedCards,
            cardId,
            assistantMessage
          );
          return updatedCards;
        });
        return response;
      } catch (error) {
        console.error("Error asking question:", error);

        // Add user message and error response
        const userMessage: ChatMessage = {
          role: "user",
          content: question,
          timestamp: new Date().toISOString(),
        };

        const errorMessage: ChatMessage = {
          role: "assistant",
          content:
            "Sorry, I encountered an error while processing your question. Please try again.",
          timestamp: new Date().toISOString(),
        };

        setCards((prevCards) => {
          let updatedCards = addMessageToCard(prevCards, cardId, userMessage);
          updatedCards = addMessageToCard(updatedCards, cardId, errorMessage);
          return updatedCards;
        });
        return errorMessage.content;
      }
    } else {
      // Fallback for when no question handler is provided
      const userMessage: ChatMessage = {
        role: "user",
        content: question,
        timestamp: new Date().toISOString(),
      };

      const fallbackMessage: ChatMessage = {
        role: "assistant",
        content:
          "I'm sorry, but the question handling feature is not currently available. Please refer to the full report for more detailed information.",
        timestamp: new Date().toISOString(),
      };

      setCards((prevCards) => {
        let updatedCards = addMessageToCard(prevCards, cardId, userMessage);
        updatedCards = addMessageToCard(updatedCards, cardId, fallbackMessage);
        return updatedCards;
      });
      return fallbackMessage.content;
    }
  };

  return (
    <div
      className={`${glassStyle.card} ${fadeInAnimation.fadeIn} ${
        isResetting ? "opacity-50" : "opacity-100"
      }`}
    >
      {/* Header with View Toggle */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Research Results
          </h2>
          <p className="text-gray-600">
            {currentView === "report"
              ? "Full comprehensive report"
              : `${cards.length} research points available for exploration`}
          </p>
        </div>
        <ViewToggle
          currentView={currentView}
          onViewChange={setCurrentView}
          className="ml-4"
        />
      </div>

      {/* Content based on current view */}
      {currentView === "report" ? (
        <ResearchReport
          output={output}
          isResetting={isResetting}
          glassStyle={glassStyle}
          fadeInAnimation={fadeInAnimation}
          loaderColor={loaderColor}
          isGeneratingPdf={isGeneratingPdf}
          isCopied={isCopied}
          onCopyToClipboard={onCopyToClipboard}
          onGeneratePdf={onGeneratePdf}
        />
      ) : (
        <div className="mt-6 -mx-6 px-2">
          {/* Expanded canvas container */}
          <div className="w-full max-w-none">
            {cards.length > 0 ? (
              <ResearchCardGrid
                cards={cards}
                onAskQuestion={handleAskQuestion}
                onRemoveCard={handleRemoveCard}
                className="min-h-screen"
              />
            ) : (
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                  <svg
                    className="w-8 h-8 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
                <p className="text-gray-500">
                  No research points available to display as cards.
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  Switch to Report View to see the full content.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedResearchReport;
