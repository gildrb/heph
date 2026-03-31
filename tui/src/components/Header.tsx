import type { SessionInfo, ArmoryInfo } from "../lib/types";

interface HeaderProps {
  session: SessionInfo | null;
  armory: ArmoryInfo | null;
  isConnected: boolean;
  isStreaming: boolean;
}

export function Header({ session, armory, isConnected, isStreaming }: HeaderProps) {
  return (
    <box flexDirection="row" padding={1} justifyContent="space-between">
      <box flexDirection="column">
        <text>
          <strong fg="yellow">Hephaistos</strong>
          {!isConnected && <span fg="red"> [Disconnected]</span>}
          {isStreaming && <span fg="cyan"> [Streaming]</span>}
        </text>
        {armory && (
          <text fg="dim">
            Armory: {armory.path ?? "none"}
            {armory.path && armory.source_file_count > 0 && ` (${armory.source_file_count} files)`}
          </text>
        )}
      </box>
      {session && (
        <box flexDirection="column" alignItems="flex-end">
          <text fg="dim">{session.model}</text>
          <text fg="dim">{session.base_url}</text>
        </box>
      )}
    </box>
  );
}
