import type { AccessLevel } from "../types.ts"

export function LevelPill({ level, label }: { level: AccessLevel; label: string }) {
  return <span className={`pill level-${level}`}>{label}</span>
}
