import { ReportPoint, ResearchCardData, ChatMessage } from "../types";

export const parseReportToCards = (
  reportContent: string
): ResearchCardData[] => {
  if (!reportContent || typeof reportContent !== "string") {
    return [];
  }

  const cards: ResearchCardData[] = [];

  // Split the report into blocks by top-level headings (#, ##, ###)
  const sections = reportContent
    .split(/(?=^#{1,3}\s)/gm)
    .filter((s) => s.trim());

  sections.forEach((section, sectionIndex) => {
    // Track the latest competitor name if we encounter lines like **Stripe:**
    let currentCompetitor: string | null = null;

    // Break section into individual lines for granular parsing
    const lines = section.split(/\n+/g);

    lines.forEach((rawLine, lineIndex) => {
      const line = rawLine.trim();
      if (!line) return;

      // Detect a competitor label like **Stripe:** or **Adyen:**
      const competitorMatch = line.match(/^\*\*(.+?)\*\*:/);
      if (competitorMatch) {
        currentCompetitor = competitorMatch[1].trim();
        return; // move to next line – nothing to card yet
      }

      // Detect bullet points that start with -, *, or •
      const bulletMatch = line.match(/^[-*•]\s+(.*)/);
      if (!bulletMatch) return; // not a bullet

      const bulletContent = bulletMatch[1].trim();

      // Inside a bullet, look for bold title followed by colon (**Title:** description)
      let bulletTitle = "";
      let bulletDescription = bulletContent;
      const boldTitleMatch = bulletContent.match(/^\*\*(.+?)\*\*:\s*(.+)/);
      if (boldTitleMatch) {
        bulletTitle = boldTitleMatch[1].trim();
        bulletDescription = boldTitleMatch[2].trim();
      } else {
        // Fallback: split by first colon if present
        const colonIdx = bulletContent.indexOf(":");
        if (colonIdx > 0) {
          bulletTitle = bulletContent.substring(0, colonIdx).trim();
          bulletDescription = bulletContent.substring(colonIdx + 1).trim();
        } else {
          bulletTitle = bulletContent;
        }
      }

      // Compose full title with competitor context if available
      const fullTitle = currentCompetitor
        ? `${currentCompetitor} ${bulletTitle}`
        : bulletTitle;

      // Push card representing this leaf bullet point
      cards.push({
        id: `${sectionIndex}-${lineIndex}`,
        title: fullTitle,
        summary:
          bulletDescription.length > 150
            ? bulletDescription.substring(0, 150) + "..."
            : bulletDescription,
        content: bulletDescription,
        chatHistory: [] as ChatMessage[],
      });
    });
  });

  // If no leaf cards detected, fall back to previous paragraph/section parsing (rare)
  if (cards.length === 0) {
    const paragraphs = reportContent.split(/\n\s*\n/).filter((p) => p.trim());
    paragraphs.forEach((paragraph, index) => {
      if (paragraph.trim().length < 50) return;
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
