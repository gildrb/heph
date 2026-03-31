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
        <text fg="dim">Start a conversation...</text>
      </box>
    );
  }

  return (
    <scrollbox flexGrow={1}>
      <box flexDirection="column" padding={1}>
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
      marginY={1}
      padding={1}
      backgroundColor={isUser ? "#1a3a1a" : "#1a1a3a"}
    >
      <text fg={isUser ? "#4ade80" : "#60a5fa"}>
        {isUser ? "You" : "Assistant"}
      </text>
      <box marginTop={1}>
        <text width="100%">
          {formattedContent || <span fg="dim">...</span>}
        </text>
      </box>
    </box>
  );
}

function StreamingIndicator() {
  return (
    <box flexDirection="column" marginY={1} padding={1} backgroundColor="#1a1a3a">
      <text fg="#60a5fa">Assistant</text>
      <box marginTop={1}>
        <text fg="cyan">▊</text>
      </box>
    </box>
  );
}
