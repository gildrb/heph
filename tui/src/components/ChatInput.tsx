import { useState } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  prompt?: string;
}

export function ChatInput({ onSend, disabled, prompt = "> " }: ChatInputProps) {
  const [value, setValue] = useState("");

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (trimmed && !disabled) {
      onSend(trimmed);
      setValue("");
    }
  };

  return (
    <box flexDirection="row" padding={1}>
      <text fg="cyan">{prompt}</text>
      <input
        value={value}
        onChange={setValue}
        placeholder="Type a message..."
        width="100%"
      />
      {value.trim() && !disabled && (
        <box
          onMouseDown={handleSubmit}
          paddingX={1}
          marginLeft={1}
        >
          <text fg="green">[Enter] Send</text>
        </box>
      )}
    </box>
  );
}
