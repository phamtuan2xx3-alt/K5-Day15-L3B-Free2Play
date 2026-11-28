export type ThemeMode = "system" | "light" | "dark";

export type ExportFormat = "anki" | "md" | "etude" | "json";

export type CardStatus = "needs_review" | "mastered";

export interface AuthUser {
  user_id: string;
  email: string;
  display_name: string;
  picture_url?: string;
}

export interface MeResponse {
  authenticated: boolean;
  user: AuthUser | null;
  guest_demo: boolean;
  guest_remaining?: number;
  oauth_configured?: boolean;
}

export interface SubmissionOption {
  id: string;
  label?: string;
  title?: string;
  category?: string;
}

export interface HardFlag {
  rule_id: string;
  file: string;
  line: number | string;
  detail: string;
  severity?: string;
}

export interface GitHubCheckStatus {
  key: "PUBLIC-ACCESS" | "GIT-FORK-PR" | "PENALTY-STANDARD" | "PENALTY-KEY" | string;
  label?: string;
  status: "pass" | "fail" | "warn" | "unknown" | string;
  detail: string;
}

export interface MemberIdentity {
  name: string;
  slug: string;
  role?: string;
  owned_scope?: string;
  tasks?: string[];
  spec_tasks?: string[];
  reflection_file?: string;
}

export interface ScanDiffSummary {
  previous_scan_id?: string | null;
  flags_delta?: number | null;
  previous_flags_count?: number | null;
  current_flags_count?: number | null;
  bloom_delta?: number | null;
  summary?: string;
}

export interface ScanSessionSummary {
  scan_id: string;
  source_type: "local" | "github" | string;
  source_label: string;
  commit_sha?: string;
  mode: "team" | "personal" | string;
  hard_flags_count?: number;
  flags_delta?: number | null;
  created_at: string;
}

export interface VivaEntry {
  id?: number;
  scan_id: string;
  member_slug: string;
  member_name: string;
  mode: "ask" | "defense" | "coach" | string;
  concept_key?: string;
  question?: string;
  answer?: string;
  ai_feedback?: string;
  bloom_level?: number | null;
  draft?: BloomDraft | null;
  draft_json?: string | BloomDraft | null;
  saved_by_user?: number | boolean;
  created_at?: string;
}

export interface ScanSessionDetail extends ScanSessionSummary {
  members: MemberIdentity[];
  default_user?: string | null;
  audit_output: string;
  hard_flags: HardFlag[];
  checks: Record<string, GitHubCheckStatus> | GitHubCheckStatus[];
  missing_required: string[];
  line_counts?: Record<string, number>;
  tracing?: Record<string, unknown>;
  viva_entries?: VivaEntry[];
  diff?: ScanDiffSummary | null;
}

export interface FileLineItem {
  line: number;
  text: string;
}

export interface FileLinesResponse {
  file: string;
  target_line?: number;
  lines: FileLineItem[];
}

export interface VivaAskResponse {
  entry_id?: number;
  question: string;
  concept_key?: string;
  term?: string;
  tag?: string;
  source_cite?: string;
  viva_meta_token?: string;
  raw_output?: string;
}

export interface BloomDraft {
  concept_key: string;
  term?: string;
  tag?: string;
  source_cite?: string;
  bloom_level: number;
  understood_points?: string[];
  missing_points?: string[];
  misconceptions?: string[];
  resolved_misconceptions?: string[];
  next_probe?: string;
  reference?: string;
  rubric?: string;
}

export interface VivaDefenseResponse {
  entry_id?: number;
  ai_feedback: string;
  bloom_level?: number | null;
  bloom_label?: string;
  draft?: BloomDraft | null;
}

export interface VivaCoachResponse {
  entry_id?: number;
  advice: string;
  question: string;
  concept_key?: string;
  term?: string;
  tag?: string;
  source_cite?: string;
  viva_meta_token?: string;
}

export interface BloomHistoryItem {
  bloom_level: number;
  timestamp?: string;
  scan_id?: string;
  note?: string;
}

export interface BloomConcept {
  concept_key: string;
  term?: string;
  tag?: string;
  source_cite?: string;
  bloom_level: number;
  highest_bloom_level?: number;
  understood_points?: string[];
  missing_points?: string[];
  misconceptions?: string[];
  resolved_misconceptions?: string[];
  next_probe?: string;
  prompt?: string;
  reference?: string;
  rubric?: string;
  status: CardStatus;
  history?: BloomHistoryItem[];
  updated_at?: string;
}

export interface MemberProfileResponse {
  member_slug: string;
  member_name?: string;
  concepts: BloomConcept[];
}

export interface HealthResponse {
  status: string;
  oauth_configured?: boolean;
  model_provider?: string;
  allow_guest_demo?: boolean;
}

export interface StreamStageEvent {
  step: string;
  label: string;
}

export interface ScanPreflightPayload {
  source_type: "local" | "github" | string;
  source_label: string;
  commit_sha?: string;
  mode: "team" | "personal" | string;
  members: MemberIdentity[];
  checks: Record<string, GitHubCheckStatus> | GitHubCheckStatus[];
  hard_flags: HardFlag[];
  missing_required: string[];
  present_files_count?: number;
  repo_profile?: string;
}

export interface ScanStreamState {
  target: string;
  stageStep: string;
  stageLabel: string;
  startedAt: number;
  preflight: ScanPreflightPayload | null;
  reasoningText: string;
  contentText: string;
}
