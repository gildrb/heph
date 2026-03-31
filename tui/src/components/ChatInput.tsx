interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: (message: string) => void;
  disabled?: boolean;
  prompt?: string;
}

export function ChatInput({ value, onChange, onSend, disabled, prompt = "› " }: ChatInputProps) {
  const handleSubmit = () => {
    const trimmed = value.trim();
    if (trimmed && !disabled) {
      onSend(trimmed);
    }
  };

  return (
    <box flexDirection="row" alignItems="center">
      <text fg="#7c87ff" bold>{prompt}</text>
      <input
        value={value}
        onChange={onChange}
        placeholder="Type a message..."
        width="100%"
        disabled={disabled}
      />
      {value.trim() && !disabled && (
        <box paddingX={2}>
          <text fg="#10b981" dim={false}>↵ send</text>
        </box>
      )}
      {disabled && (
        <box paddingX={2}>
          <text fg="#737373">waiting...</text>
        </box>
      )}
    </box>
  );
}
