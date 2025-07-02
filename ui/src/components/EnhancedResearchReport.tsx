import { useState, useEffect } from "react";
import {
  ResearchOutput,
  ResearchCardData,
  ChatMessage,
  GlassStyle,
} from "../types";
import { Link } from "react-router-dom";
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
  const [cards, setCards] = useState<ResearchCardData[]>([]);

  // Parse report into cards when output changes
  useEffect(() => {
    if (output?.details?.report) {
      const parsedCards = parseReportToCards(output.details.report);
      setCards(parsedCards);
    }
  }, [output?.details?.report]);

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
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Research Results
        </h2>
        <p className="text-gray-600">
          Click on a section below to deep dive into more details.
        </p>

        {/* Deep Dive Links */}
        {cards.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-4">
            {cards.map((card) => (
              <Link
                key={card.id}
                to={`/deep-dive/${card.id}`}
                state={{ card }}
                className="px-3 py-1.5 rounded-lg bg-[#468BFF] text-white text-sm hover:bg-[#8FBCFA] transition-colors"
              >
                {card.title}
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Always show the full report below */}
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
        cards={cards}
      />
    </div>
  );
};

export default EnhancedResearchReport;
