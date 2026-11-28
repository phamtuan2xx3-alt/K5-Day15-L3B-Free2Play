import { useEffect, useMemo, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { BookmarkCheck, Eye, EyeOff, MessageSquare, RotateCcw, Send, TrendingUp, X } from "lucide-react";
import { confirmStudyLog, vivaChatStream } from "@/api/client.ts";
import { CiteText } from "@/components/CiteText.tsx";
import { InlineMarkdown, MarkdownView } from "@/components/MarkdownView.tsx";
import { Alert } from "@/components/ui/alert.tsx";
import { Badge } from "@/components/ui/badge.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Textarea } from "@/components/ui/textarea.tsx";
import type {
  BloomConcept,
  BloomDraft,
  ScanSessionDetail,
  VivaChatHistoryItem,
  VivaChatMode,
} from "@/types.ts";
import type { VivaStarterQuestion } from "@/utils/auditSections.ts";
import { BLOOM_LABELS } from "@/utils/citations.ts";

interface VivaStudyPanelProps {
  session: ScanSessionDetail;
  starterQuestions?: VivaStarterQuestion[];
  drillConcept?: BloomConcept | null;
  onSelectCite: (file: string, line: number) => void;
  onKnowledgeSaved?: () => void;
  onConsumeDrillConcept?: () => void;
}

interface ChatTurn {
  id: string;
  role: "assistant" | "user";
  kind: "question" | "answer" | "diagnosis" | "tutor";
  content: string;
  entryId?: number;
  bloomLevel?: number | null;
  bloomLabel?: string;
  draft?: BloomDraft | null;
  conceptKey?: string;
  term?: string;
  tag?: string;
  sourceCite?: string;
  vivaMetaToken?: string;
  saved?: boolean;
}

interface VivaStreamState {
  action: VivaChatMode;
  stageLabel: string;
  startedAt: number;
  reasoningText: string;
  contentText: string;
}

function stripStreamingMeta(raw: string): string {
  return (raw || "").replace(/\[(?:VIVA_META_JSON|BLOOM_LOG_DRAFT_JSON)[\s\S]*$/i, "").trim();
}

function isHelpIntent(msg: string): boolean {
  const low = msg.toLowerCase();
  if (/b[oỏ]\s+qua|ch[aấ]m\s*10|level\s*6|<script/i.test(low)) return false;
  return /\b(?:gi[uú]p|gi[aả]i\s*th[ií]ch|h[uư][oớ]ng\s*d[aẫ]n|ch[uư]a\s*hi[eể]u|kh[oó]\s*hi[eể]u|n[aâ]ng\s*(?:b[aậ]c|bloom)|g[oợ]i\s*[yý])\b/i.test(
    low,
  );
}

export function VivaStudyPanel({
  session,
  starterQuestions = [],
  drillConcept = null,
  onSelectCite,
  onKnowledgeSaved,
  onConsumeDrillConcept,
}: VivaStudyPanelProps) {
  const defaultMember = useMemo(() => {
    if (session.default_user) return session.default_user;
    if (session.members.length === 1) return session.members[0].name;
    return session.members[0]?.name || "Người dùng cá nhân";
  }, [session]);

  const [selectedMember, setSelectedMember] = useState<string>(defaultMember);
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [answerText, setAnswerText] = useState<string>("");
  const [revealedTurnId, setRevealedTurnId] = useState<string | null>(null);

  const [busyMode, setBusyMode] = useState<VivaChatMode | "confirm" | null>(null);
  const [vivaStream, setVivaStream] = useState<VivaStreamState | null>(null);
  const [elapsedSec, setElapsedSec] = useState(0);
  const abortRef = useRef<AbortController | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!vivaStream) {
      setElapsedSec(0);
      return;
    }
    setElapsedSec(Math.max(0, Math.floor((Date.now() - vivaStream.startedAt) / 1000)));
    const id = window.setInterval(() => {
      setElapsedSec(Math.max(0, Math.floor((Date.now() - vivaStream.startedAt) / 1000)));
    }, 1000);
    return () => window.clearInterval(id);
  }, [vivaStream?.startedAt]);

  useEffect(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setSelectedMember(defaultMember);
    setTurns([]);
    setAnswerText("");
    setRevealedTurnId(null);
    setVivaStream(null);
    setBusyMode(null);
    setErrorMsg(null);
    setStatusMsg(null);
  }, [session.scan_id, defaultMember]);

  // Preload concept drilled from Tab 3 (Hệ thống kiến thức)
  useEffect(() => {
    if (!drillConcept) return;
    if (drillConcept.source_repo && drillConcept.source_repo !== session.source_label) return;
    const qText =
      drillConcept.next_probe ||
      drillConcept.prompt ||
      `Hãy diễn đạt lại bằng lời của bạn cơ chế & bằng chứng cho khái niệm "${drillConcept.term || drillConcept.concept_key}" (hiện ở L${drillConcept.bloom_level}/6).`;
    setTurns([
      {
        id: `drill-${Date.now()}`,
        role: "assistant",
        kind: "question",
        content: qText,
        conceptKey: drillConcept.concept_key,
        term: drillConcept.term,
        tag: drillConcept.tag,
        sourceCite: drillConcept.source_cite,
        draft: {
          concept_key: drillConcept.concept_key,
          term: drillConcept.term,
          tag: drillConcept.tag,
          source_cite: drillConcept.source_cite,
          bloom_level: drillConcept.bloom_level,
          reference: drillConcept.reference,
          rubric: drillConcept.rubric,
        },
      },
    ]);
    setStatusMsg(`Đang ôn lại khái niệm "${drillConcept.term || drillConcept.concept_key}" (L${drillConcept.bloom_level}/6).`);
    onConsumeDrillConcept?.();
  }, [drillConcept, session.source_label, onConsumeDrillConcept]);

  useEffect(() => {
    if (turns.length === 0 && !vivaStream) return;
    chatEndRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [turns.length, vivaStream]);

  const activeContext = useMemo(() => {
    for (let i = turns.length - 1; i >= 0; i -= 1) {
      const t = turns[i];
      if (t.role === "assistant") {
        return {
          concept_key: t.conceptKey || t.draft?.concept_key,
          term: t.term || t.draft?.term,
          tag: t.tag || t.draft?.tag,
          source_cite: t.sourceCite || t.draft?.source_cite,
          reference: t.draft?.reference,
          rubric: t.draft?.rubric,
          question: t.kind === "question" || t.kind === "tutor" ? t.content : t.draft?.next_probe,
          vivaMetaToken: t.vivaMetaToken,
        };
      }
    }
    return null;
  }, [turns]);

  const buildHistory = (list: ChatTurn[]): VivaChatHistoryItem[] =>
    list.slice(-8).map((t) => ({ role: t.role, content: t.content }));

  const handleCancelStream = () => {
    abortRef.current?.abort();
    abortRef.current = null;
    setVivaStream(null);
    setBusyMode(null);
  };

  const runChatAction = async (
    mode: VivaChatMode,
    message: string,
    existingTurns: ChatTurn[],
  ) => {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setBusyMode(mode);
    setErrorMsg(null);
    setStatusMsg(null);
    setRevealedTurnId(null);

    const stageLabel =
      mode === "tutor"
        ? "Gia sư AI đang giải thích & gợi ý nâng +1 Bloom…"
        : mode === "start" || mode === "next"
          ? "Đang soạn 1 câu hỏi ngắn bám repo…"
          : "Đang chấm mức hiểu Bloom L0–L6…";

    setVivaStream({
      action: mode,
      stageLabel,
      startedAt: Date.now(),
      reasoningText: "",
      contentText: "",
    });

    try {
      const ctx = activeContext;
      const res = await vivaChatStream(
        {
          scan_id: session.scan_id,
          member_name: selectedMember,
          mode,
          message,
          history: buildHistory(existingTurns),
          active_concept: ctx
            ? {
                concept_key: ctx.concept_key,
                term: ctx.term,
                tag: ctx.tag,
                source_cite: ctx.source_cite,
                reference: ctx.reference,
                rubric: ctx.rubric,
                question: ctx.question,
              }
            : undefined,
          viva_meta: ctx?.vivaMetaToken,
        },
        {
          signal: ctrl.signal,
          onStage: (ev) =>
            setVivaStream((prev) => (prev ? { ...prev, stageLabel: ev.label || prev.stageLabel } : prev)),
          onReasoning: (delta) =>
            setVivaStream((prev) => (prev ? { ...prev, reasoningText: prev.reasoningText + delta } : prev)),
          onContent: (delta) =>
            setVivaStream((prev) => (prev ? { ...prev, contentText: prev.contentText + delta } : prev)),
        },
      );
      if (ctrl.signal.aborted) return;
      setVivaStream(null);

      const newTurn: ChatTurn = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        kind: mode === "answer" ? "diagnosis" : mode === "tutor" ? "tutor" : "question",
        content: res.reply_text || res.question || "",
        entryId: res.entry_id,
        bloomLevel: res.bloom_level ?? null,
        bloomLabel: res.bloom_label,
        draft: res.draft ?? null,
        conceptKey: res.concept_key,
        term: res.term,
        tag: res.tag,
        sourceCite: res.source_cite,
        vivaMetaToken: res.viva_meta_token,
      };
      setTurns((prev) => [...prev, newTurn]);
    } catch (err) {
      setVivaStream(null);
      if ((err instanceof DOMException && err.name === "AbortError") || ctrl.signal.aborted) return;
      setErrorMsg(err instanceof Error ? err.message : "Không kết nối được lượt vấn đáp.");
    } finally {
      if (abortRef.current === ctrl) {
        abortRef.current = null;
        setBusyMode(null);
      }
    }
  };

  const handleStartQuestion = () => {
    void runChatAction("start", "", turns);
  };

  const handlePickStarter = (q: VivaStarterQuestion) => {
    const pickedTurn: ChatTurn = {
      id: `starter-${Date.now()}`,
      role: "assistant",
      kind: "question",
      content: q.question,
      conceptKey: q.id,
      term: q.targetMember || "Câu hỏi gợi ý",
      sourceCite: q.sourceCite,
    };
    setErrorMsg(null);
    setStatusMsg(null);
    setTurns((prev) => [...prev, pickedTurn]);
  };

  const handleSubmitMessage = async (e?: FormEvent) => {
    e?.preventDefault();
    const trimmed = answerText.trim();
    if (!trimmed || busyMode !== null) return;

    const userTurn: ChatTurn = {
      id: `usr-${Date.now()}`,
      role: "user",
      kind: "answer",
      content: trimmed,
    };
    const nextTurns = [...turns, userTurn];
    setTurns(nextTurns);
    setAnswerText("");

    if (turns.length === 0) {
      await runChatAction("start", trimmed, nextTurns);
      return;
    }

    const hasPriorDiagnosis = turns.some((t) => t.kind === "diagnosis" || t.kind === "tutor");
    const chosenMode: VivaChatMode = hasPriorDiagnosis && isHelpIntent(trimmed) ? "tutor" : "answer";
    await runChatAction(chosenMode, trimmed, nextTurns);
  };

  const handleComposerKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSubmitMessage();
    }
  };

  const handleSaveToKnowledge = async (turn: ChatTurn) => {
    if (!turn.draft && !turn.entryId) return;
    setBusyMode("confirm");
    setErrorMsg(null);
    try {
      await confirmStudyLog({
        scan_id: session.scan_id,
        member_name: selectedMember,
        entry_id: turn.entryId,
        draft: turn.draft ?? undefined,
      });
      setTurns((prev) => prev.map((t) => (t.id === turn.id ? { ...t, saved: true } : t)));
      setStatusMsg("Đã lưu kiến thức & mức Bloom vào Hệ thống kiến thức.");
      onKnowledgeSaved?.();
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Không lưu được vào Hệ thống kiến thức.");
    } finally {
      setBusyMode(null);
    }
  };

  const hasConversation = turns.length > 0 || vivaStream !== null;

  return (
    <div id="viva-chat-shell" className="tabpanel-inner mx-auto w-full max-w-[1040px] space-y-5">
      {/* Operate-mode Header matching AuditPanel & KnowledgeHubPanel */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="m-0 text-lg font-semibold tracking-tight text-foreground">
            Vấn đáp: {session.source_label}
          </h2>
          <p className="m-0 mt-0.5 text-xs text-muted-foreground">
            Hỏi từng câu ngắn bám sát repo và chấm mức hiểu Bloom L0–L6 cho{" "}
            <strong className="text-foreground">{selectedMember}</strong>.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {session.mode === "team" && session.members.length >= 2 ? (
            <div className="flex items-center gap-1.5">
              <label htmlFor="viva-member-select" className="text-xs font-medium text-muted-foreground">
                Thành viên
              </label>
              <select
                id="viva-member-select"
                className="h-8 rounded-md border border-input bg-background px-2 text-xs font-medium text-foreground"
                value={selectedMember}
                onChange={(e) => setSelectedMember(e.target.value)}
              >
                {session.members.map((m) => (
                  <option key={m.slug || m.name} value={m.name}>
                    {m.name}
                    {m.role ? ` (${m.role})` : ""}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <Badge variant="outline">{selectedMember}</Badge>
          )}

          {!hasConversation ? (
            <Button type="button" size="sm" disabled={busyMode !== null} onClick={handleStartQuestion}>
              <MessageSquare aria-hidden="true" className="h-3.5 w-3.5" />
              Bắt đầu kiểm tra kiến thức
            </Button>
          ) : (
            <>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                disabled={busyMode !== null}
                onClick={() => void runChatAction("next", "", turns)}
              >
                <MessageSquare aria-hidden="true" className="h-3.5 w-3.5" />
                Câu hỏi mới
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={busyMode !== null}
                onClick={() => {
                  setTurns([]);
                  setStatusMsg(null);
                  setErrorMsg(null);
                }}
              >
                <RotateCcw aria-hidden="true" className="h-3.5 w-3.5" />
                Làm mới chat
              </Button>
            </>
          )}
        </div>
      </div>

      {errorMsg && (
        <Alert variant="destructive" role="alert">
          {errorMsg}
        </Alert>
      )}
      {statusMsg && (
        <Alert variant="success" role="status" aria-live="polite">
          {statusMsg}
        </Alert>
      )}

      {!hasConversation ? (
        starterQuestions.length > 0 ? (
          <section aria-labelledby="viva-starter-heading" className="space-y-2.5">
            <h3 id="viva-starter-heading" className="m-0 text-sm font-medium text-foreground">
              Câu hỏi gợi ý từ lần soi repo
            </h3>
            <div className="grid gap-2.5 sm:grid-cols-2">
              {starterQuestions.map((sq, idx) => (
                <button
                  key={sq.id}
                  type="button"
                  onClick={() => handlePickStarter(sq)}
                  className="group flex flex-col gap-1.5 rounded-lg border border-border bg-card p-3.5 text-left hover:border-primary/50 hover:bg-accent/40 active:scale-[0.99] transition-[border-color,background-color,transform] duration-150 ease-[cubic-bezier(0.23,1,0.32,1)] cursor-pointer"
                >
                  <div className="flex flex-wrap items-center justify-between gap-1.5">
                    <span className="text-xs font-semibold text-primary">
                      {sq.targetMember ? `Dành cho ${sq.targetMember}` : `Câu hỏi gợi ý ${idx + 1}`}
                    </span>
                    {sq.sourceCite ? (
                      <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground">
                        {sq.sourceCite}
                      </code>
                    ) : null}
                  </div>
                  <span className="text-xs leading-relaxed text-foreground/90">
                    <InlineMarkdown text={sq.question} />
                  </span>
                </button>
              ))}
            </div>
          </section>
        ) : null
      ) : (
        <div
          className="rounded-xl border border-border bg-card p-4 sm:p-5 space-y-4"
          aria-live="polite"
        >
          {turns.map((turn) => {
            if (turn.role === "user") {
              return (
                <div key={turn.id} className="flex justify-end">
                  <div className="max-w-[82%] rounded-2xl rounded-br-sm border border-primary/25 bg-primary/10 px-4 py-2.5 text-sm text-foreground">
                    <p className="m-0 whitespace-pre-wrap leading-relaxed">{turn.content}</p>
                  </div>
                </div>
              );
            }

            const isDiagnosis = turn.kind === "diagnosis";
            const showReveal = revealedTurnId === turn.id;
            const refText = turn.draft?.reference;
            const rubricText = turn.draft?.rubric;
            const citeText = turn.draft?.source_cite || turn.sourceCite;
            const nextLevel =
              typeof turn.bloomLevel === "number" ? Math.min(6, turn.bloomLevel + 1) : 2;

            return (
              <div key={turn.id} className="flex items-start gap-3">
                <img
                  src="/repoksv-logo-120.png"
                  alt=""
                  width={28}
                  height={28}
                  className="brand-logo mt-0.5 border border-border bg-card p-0.5"
                />
                <div
                  className={
                    isDiagnosis
                      ? "feedback-box min-w-0 flex-1 rounded-xl border border-border bg-background/60 p-4 space-y-2.5"
                      : "min-w-0 flex-1 rounded-xl border border-border/80 bg-muted/25 p-4 space-y-2"
                  }
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <strong className="text-xs font-semibold text-foreground">
                        {turn.kind === "tutor"
                          ? "Gia sư Bloom"
                          : isDiagnosis
                            ? "Đánh giá Bloom"
                            : "Câu hỏi phản biện"}
                      </strong>
                      {turn.term ? <Badge variant="warning">{turn.term}</Badge> : null}
                      {citeText ? <CiteText text={citeText} onSelectCite={onSelectCite} /> : null}
                    </div>

                    {typeof turn.bloomLevel === "number" ? (
                      <div className="flex items-center gap-1.5">
                        <Badge>Level {turn.bloomLevel}/6</Badge>
                        <span className="text-xs text-muted-foreground">
                          {turn.bloomLabel || BLOOM_LABELS[turn.bloomLevel]}
                        </span>
                      </div>
                    ) : null}
                  </div>

                  <div className="max-w-[74ch] text-sm leading-relaxed text-foreground">
                    <MarkdownView text={turn.content} onSelectCite={onSelectCite} />
                  </div>

                  {isDiagnosis ? (
                    <div className="flex flex-wrap items-center gap-2 border-t border-border/60 pt-2.5">
                      {typeof turn.bloomLevel === "number" && turn.bloomLevel < 6 ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="secondary"
                          className="rounded-full h-8 text-xs"
                          disabled={busyMode !== null}
                          onClick={() =>
                            void runChatAction(
                              "tutor",
                              `Giải thích giúp mình bản chất và cách nâng câu này lên Level ${nextLevel}/6.`,
                              turns,
                            )
                          }
                        >
                          <TrendingUp aria-hidden="true" className="h-3.5 w-3.5" />
                          Giúp mình nâng lên Level {nextLevel}
                        </Button>
                      ) : null}

                      <Button
                        type="button"
                        size="sm"
                        variant="teal"
                        className="rounded-full h-8 text-xs"
                        disabled={busyMode !== null || Boolean(turn.saved)}
                        onClick={() => void handleSaveToKnowledge(turn)}
                      >
                        <BookmarkCheck aria-hidden="true" className="h-3.5 w-3.5" />
                        {turn.saved ? "Đã lưu" : "Lưu vào Hệ thống kiến thức"}
                      </Button>

                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        className="rounded-full h-8 text-xs"
                        disabled={busyMode !== null}
                        onClick={() => void runChatAction("next", "", turns)}
                      >
                        Hỏi ý tiếp theo
                      </Button>

                      {refText || rubricText ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          className="rounded-full h-8 text-xs"
                          onClick={() => setRevealedTurnId(showReveal ? null : turn.id)}
                        >
                          {showReveal ? (
                            <EyeOff aria-hidden="true" className="h-3.5 w-3.5" />
                          ) : (
                            <Eye aria-hidden="true" className="h-3.5 w-3.5" />
                          )}
                          {showReveal ? "Ẩn đáp án" : "Đáp án gợi ý"}
                        </Button>
                      ) : null}
                    </div>
                  ) : null}

                  {showReveal && (refText || rubricText) ? (
                    <Alert variant="info" className="space-y-1 text-xs">
                      {refText ? (
                        <div>
                          <strong>Điểm chốt:</strong>{" "}
                          <InlineMarkdown text={refText} onSelectCite={onSelectCite} />
                        </div>
                      ) : null}
                      {rubricText ? (
                        <div>
                          <strong>Tiêu chí đạt:</strong>{" "}
                          <InlineMarkdown text={rubricText} onSelectCite={onSelectCite} />
                        </div>
                      ) : null}
                    </Alert>
                  ) : null}
                </div>
              </div>
            );
          })}

          {/* Live Streaming Bubble */}
          {vivaStream ? (
            <div className="flex items-start gap-3">
              <img
                src="/repoksv-logo-120.png"
                alt=""
                width={28}
                height={28}
                className="brand-logo mt-0.5 border border-border bg-card p-0.5"
              />
              <div className="min-w-0 flex-1 rounded-xl border border-primary/40 bg-background/60 p-4 space-y-2.5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="stream-dot shrink-0" aria-hidden="true" />
                    <strong className="text-xs text-foreground truncate">{vivaStream.stageLabel}</strong>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="default" className="font-mono tabular-nums">
                      {elapsedSec}s
                    </Badge>
                    <Button type="button" size="sm" variant="outline" onClick={handleCancelStream}>
                      <X aria-hidden="true" className="h-3.5 w-3.5" />
                      Huỷ
                    </Button>
                  </div>
                </div>

                {vivaStream.reasoningText ? (
                  <details className="disclosure" open={!stripStreamingMeta(vivaStream.contentText)}>
                    <summary>
                      Suy luận của AI ({vivaStream.reasoningText.length.toLocaleString("vi-VN")} ký tự)
                    </summary>
                    <pre className="m-0 max-h-40 overflow-y-auto scroller whitespace-pre-wrap break-words rounded border border-border/70 bg-muted/40 p-2 font-mono text-xs text-muted-foreground">
                      {vivaStream.reasoningText}
                    </pre>
                  </details>
                ) : null}

                <div className="max-w-[74ch] text-sm">
                  {stripStreamingMeta(vivaStream.contentText) ? (
                    <MarkdownView text={stripStreamingMeta(vivaStream.contentText)} onSelectCite={onSelectCite} />
                  ) : (
                    <p className="m-0 text-xs text-muted-foreground">Đang chờ token phản hồi từ AI…</p>
                  )}
                </div>
              </div>
            </div>
          ) : null}

          <div ref={chatEndRef} />
        </div>
      )}

      {/* Composer */}
      <form
        onSubmit={(e) => void handleSubmitMessage(e)}
        className={
          hasConversation
            ? "sticky bottom-0 z-10 bg-background/95 pt-2 pb-1 backdrop-blur-xs"
            : "pt-1"
        }
      >
        <div className="rounded-xl border border-input bg-card shadow-2xs transition-colors focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/15">
          <label htmlFor="viva-answer-box" className="sr-only">
            Câu trả lời vấn đáp hoặc yêu cầu nâng Bloom
          </label>
          <Textarea
            id="viva-answer-box"
            name="answer"
            className="min-h-[56px] max-h-40 w-full resize-none border-0 bg-transparent px-3.5 pt-3 pb-1 text-sm shadow-none focus-visible:outline-none"
            value={answerText}
            onChange={(e) => setAnswerText(e.target.value)}
            onKeyDown={handleComposerKeyDown}
            placeholder={
              turns.length === 0
                ? "Nhập chủ đề muốn kiểm tra kiến thức hoặc chọn câu hỏi gợi ý ở trên…"
                : 'Nhập câu trả lời (kèm file:Lxx) hoặc nhắn "giải thích giúp mình"...'
            }
          />
          <div className="flex flex-wrap items-center justify-between gap-2 px-3 pb-2.5 pt-1">
            <span className="text-[11px] text-muted-foreground">
              {turns.length === 0
                ? "Gửi trực tiếp để AI hỏi theo chủ đề bạn nhập"
                : "Enter để gửi · Shift+Enter xuống dòng"}
            </span>
            <Button
              type="submit"
              size="sm"
              disabled={busyMode !== null || !answerText.trim()}
              className="h-8 rounded-lg px-3"
            >
              <Send aria-hidden="true" className="h-3.5 w-3.5" />
              Gửi trả lời
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
