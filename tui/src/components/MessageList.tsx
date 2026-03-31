import type { Message } from "../lib/types";

function stripAnsi(text: string): string {
  return text.replace(/\x1b\[[0-9;]*[a-zA-Z]/g, "");
}

function formatContent(content: string): string {
  const cleaned = stripAnsi(content);
  return cleaned.trim();
}

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
}

export function MessageList({ messages, isStreaming }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <box flexGrow={1} justifyContent="center" alignItems="center">
        <box flexDirection="column" alignItems="center">
          <text fg="#525252" bold>Hephaistos</text>
          <text fg="#404040" paddingTop={1}>Start a conversation</text>
        </box>
      </box>
    );
  }

  return (
    <scrollbox flexGrow={1} padding={1}>
      <box flexDirection="column" gap={1}>
        {messages.map((msg) => (
          <MessageItem key={msg.id} message={msg} />
        ))}
        {isStreaming && <StreamingIndicator />}
      </box>
    </scrollbox>
  );
}

function MessageItem({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const formattedContent = formatContent(message.content);

  return (
    <box
      flexDirection="column"
      padding={2}
      backgroundColor={isUser ? "#1a1f1a" : "#1a1a1f"}
      borderColor={isUser ? "#22c55e33" : "#7c87ff33"}
      border={1}
      marginY={1}
    >
      <text fg={isUser ? "#22c55e" : "#7c87ff"} bold>
        {isUser ? "You" : "Assistant"}
      </text>
      <box marginTop={1}>
        <text width="100%" fg="#e5e5e5">
          {formattedContent || <span fg="#525252">...</span>}
        </text>
      </box>
    </box>
  );
}

function StreamingIndicator() {
  return (
    <box
      flexDirection="column"
      padding={2}
      backgroundColor="#1a1a1f"
      borderColor="#7c87ff33"
      border={1}
      marginY={1}
    >
      <text fg="#7c87ff" bold>Assistant</text>
      <box marginTop={1}>
        <text fg="#7c87ff">▊</text>
      </box>
    </box>
  );
}
