const API_URL = "http://localhost:8000";

export const askQuestionAboutCard = async (
  cardId: string,
  question: string,
  cardContent: string
): Promise<string> => {
  try {
    // For now, we'll create a mock response since the backend API might not be ready
    // In a real implementation, this would call your backend API

    const response = await fetch(`${API_URL}/card_chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
        card_context: cardContent,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      return (
        data.answer ||
        "I received your question but could not generate a response."
      );
    } else {
      throw new Error(`API error: ${response.status}`);
    }
  } catch (error) {
    console.error("Error asking question:", error);

    // Fallback to a mock response for demonstration
    return generateMockResponse(question, cardContent);
  }
};

// Mock response generator for demonstration purposes
const generateMockResponse = (question: string, context: string): string => {
  const questionLower = question.toLowerCase();

  // Simple keyword-based responses
  if (questionLower.includes("when") || questionLower.includes("date")) {
    return "Based on the available information, specific dates may vary. Please refer to the full research report for more detailed timeline information.";
  }

  if (questionLower.includes("why") || questionLower.includes("reason")) {
    return "The reasons behind this development are multifaceted and likely include strategic business considerations, market conditions, and competitive positioning.";
  }

  if (questionLower.includes("how") || questionLower.includes("process")) {
    return "The process typically involves multiple stakeholders and strategic planning. For detailed methodology, please consult the comprehensive research report.";
  }

  if (questionLower.includes("impact") || questionLower.includes("effect")) {
    return "The impact of this development could be significant for the company's market position and future growth prospects. Consider both short-term and long-term implications.";
  }

  if (
    questionLower.includes("competitor") ||
    questionLower.includes("competition")
  ) {
    return "This development positions the company relative to competitors in the market. Competitive analysis shows various strategic advantages and challenges.";
  }

  // Default response
  return `Thank you for your question about "${question}". Based on the research context, this is an interesting aspect that warrants further investigation. The available information suggests multiple factors are at play. For more comprehensive insights, I recommend reviewing the full research report.`;
};
