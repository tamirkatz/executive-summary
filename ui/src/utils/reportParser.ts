import { ReportPoint, ResearchCardData, ChatMessage } from "../types";

export const parseReportToCards = (
  reportContent: string
): ResearchCardData[] => {
  if (!reportContent || typeof reportContent !== "string") {
    return [];
  }

  const cards: ResearchCardData[] = [];

  // Split the report by common section markers
  const sections = reportContent
    .split(/(?=^#{1,3}\s)/gm)
    .filter((section) => section.trim());

  sections.forEach((section, index) => {
    // Extract title from markdown headers
    const titleMatch = section.match(/^#{1,3}\s+(.+?)$/m);
    const title = titleMatch ? titleMatch[1].trim() : `Section ${index + 1}`;

    // Remove the title from content
    const content = section.replace(/^#{1,3}\s+.+?$/m, "").trim();

    if (!content) return; // Skip empty sections

    // Look for bullet points or key insights
    const bulletPoints = content.match(/^[-*•]\s+(.+?)(?=\n[-*•]|\n\n|$)/gm);

    if (bulletPoints && bulletPoints.length > 0) {
      // Create individual cards for each bullet point
      bulletPoints.forEach((bullet, bulletIndex) => {
        const bulletContent = bullet.replace(/^[-*•]\s+/, "").trim();

        // Extract the main topic (everything before the first colon)
        const colonIndex = bulletContent.indexOf(":");
        const bulletTitle =
          colonIndex > 0
            ? bulletContent.substring(0, colonIndex).trim()
            : `${title} - Point ${bulletIndex + 1}`;

        const bulletDescription =
          colonIndex > 0
            ? bulletContent.substring(colonIndex + 1).trim()
            : bulletContent;

        cards.push({
          id: `${index}-${bulletIndex}`,
          title: bulletTitle,
          summary:
            bulletDescription.length > 150
              ? bulletDescription.substring(0, 150) + "..."
              : bulletDescription,
          content: bulletDescription,
          chatHistory: [] as ChatMessage[],
        });
      });
    } else {
      // Create a single card for the entire section
      const summary =
        content.length > 200 ? content.substring(0, 200) + "..." : content;

      cards.push({
        id: `section-${index}`,
        title,
        summary,
        content,
        chatHistory: [] as ChatMessage[],
      });
    }
  });

  // If no sections were found, try to parse by paragraphs
  if (cards.length === 0) {
    const paragraphs = reportContent.split(/\n\s*\n/).filter((p) => p.trim());

    paragraphs.forEach((paragraph, index) => {
      if (paragraph.trim().length < 50) return; // Skip very short paragraphs

      // Try to extract a title from the first sentence
      const sentences = paragraph.split(/[.!?]+/);
      const firstSentence = sentences[0]?.trim();
      const title =
        firstSentence && firstSentence.length < 100
          ? firstSentence
          : `Research Point ${index + 1}`;

      const summary =
        paragraph.length > 200
          ? paragraph.substring(0, 200) + "..."
          : paragraph;

      cards.push({
        id: `paragraph-${index}`,
        title,
        summary,
        content: paragraph.trim(),
        chatHistory: [] as ChatMessage[],
      });
    });
  }

  return cards;
};

export const addMessageToCard = (
  cards: ResearchCardData[],
  cardId: string,
  message: ChatMessage
): ResearchCardData[] => {
  return cards.map((card) =>
    card.id === cardId
      ? { ...card, chatHistory: [...card.chatHistory, message] }
      : card
  );
};
