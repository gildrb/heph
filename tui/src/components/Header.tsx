import type { SessionInfo, ArmoryInfo } from "../lib/types";

interface HeaderProps {
  session: SessionInfo | null;
  armory: ArmoryInfo | null;
  isConnected: boolean;
  isStreaming: boolean;
}

export function Header({ session, armory, isConnected, isStreaming }: HeaderProps) {
  const statusDot = !isConnected ? "●" : isStreaming ? "●" : "●";
  const statusColor = !isConnected ? "#ef4444" : isStreaming ? "#7c87ff" : "#22c55e";

  return (
    <box flexDirection="row" paddingX={2} paddingY={1} justifyContent="space-between" backgroundColor="#141414">
      <box flexDirection="column">
        <text>
          <span fg="#fafafa" bold>Hephaistos</span>
          <span fg={statusColor}> {statusDot}</span>
        </text>
        {armory && (
          <text fg="#737373" paddingTop={1}>
            {armory.path?.split("/").pop() ?? "no armory"}
            {armory.source_file_count > 0 && ` · ${armory.source_file_count} files`}
          </text>
        )}
      </box>
      {session && (
        <box flexDirection="column" alignItems="flex-end">
          <text fg="#a3a3a3">{session.model}</text>
          <text fg="#525252">{session.base_url}</text>
        </box>
      )}
    </box>
  );
}
