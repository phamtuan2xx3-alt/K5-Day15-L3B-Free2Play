import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { BookmarkCheck, Check, Eye, EyeOff, MessageSquare, RotateCcw, TrendingUp, X } from "lucide-react";
import {
  confirmStudyLog,
  getMemberProfile,
  updateCardStatus,
  vivaAskStream,
  vivaCoachStream,
  vivaDefenseStream,
} from "@/api/client.ts";
import { CiteText } from "@/components/CiteText.tsx";
import { InlineMarkdown, MarkdownView } from "@/components/MarkdownView.tsx";
import { Alert } from "@/components/ui/alert.tsx";
import { Badge } from "@/components/ui/badge.tsx";
import { Button } from "@/components/ui/button.tsx";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card.tsx";
import { Input } from "@/components/ui/input.tsx";
import { Textarea } from "@/components/ui/textarea.tsx";
import { cn } from "@/lib/utils.ts";
import type {
  BloomConcept,
  BloomDraft,
  CardStatus,
  MemberProfileResponse,
  ScanSessionDetail,
  VivaDefenseResponse,
} from "@/types.ts";
import { BLOOM_LABELS, slugifyMember } from "@/utils/citations.ts";

interface VivaStudyPanelProps {
  session: ScanSessionDetail;
  onSelectCite: (file: string, line: number) => void;
}

interface ActiveCard {
  entryId?: number;
  mode: "ask" | "coach" | "queue";
  question: string;
  advice?: string;
  conceptKey?: string;
  term?: string;
  tag?: string;
  sourceCite?: string;
  vivaMetaToken?: string;
  hiddenReference?: string;
  hiddenRubric?: string;
}

interface VivaStreamState {
  action: "ask" | "coach" | "defense";
  stageLabel: string;
  startedAt: number;
  reasoningText: string;
  contentText: string;
}

function stripStreamingMeta(raw: string): string {
  return (raw || "").replace(/\[(?:VIVA_META_JSON|BLOOM_LOG_DRAFT_JSON)[\s\S]*$/i, "").trim();
}

export function VivaStudyPanel({ session, onSelectCite }: VivaStudyPanelProps) {
  const defaultMember = useMemo(() => {
    if (session.default_user) return session.default_user;
    if (session.members.length === 1) return session.members[0].name;
    return session.members[0]?.name || "Người dùng cá nhân";
  }, [session]);

  const [selectedMember, setSelectedMember] = useState<string>(defaultMember);
  const [topic, setTopic] = useState<string>("");
  const [profile, setProfile] = useState<MemberProfileResponse | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);

  const [activeCard, setActiveCard] = useState<ActiveCard | null>(null);
  const [answerText, setAnswerText] = useState<string>("");
  const [defenseResult, setDefenseResult] = useState<VivaDefenseResponse | null>(null);
  const [revealAnswer, setRevealAnswer] = useState<boolean>(false);
  const [savedConfirmed, setSavedConfirmed] = useState<boolean>(false);

  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [vivaStream, setVivaStream] = useState<VivaStreamState | null>(null);
  const [vivaElapsedSec, setVivaElapsedSec] = useState(0);
  const vivaAbortRef = useRef<AbortController | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!vivaStream) {
      setVivaElapsedSec(0);
      return;
    }
    setVivaElapsedSec(Math.max(0, Math.floor((Date.now() - vivaStream.startedAt) / 1000)));
    const id = window.setInterval(() => {
      setVivaElapsedSec(Math.max(0, Math.floor((Date.now() - vivaStream.startedAt) / 1000)));
    }, 1000);
    return () => window.clearInterval(id);
  }, [vivaStream?.startedAt]);

  useEffect(() => {
    vivaAbortRef.current?.abort();
    vivaAbortRef.current = null;
    setSelectedMember(defaultMember);
    setActiveCard(null);
    setDefenseResult(null);
    setVivaStream(null);
    setBusyAction(null);
    setAnswerText("");
    setRevealAnswer(false);
    setSavedConfirmed(false);
    setErrorMsg(null);
    setStatusMsg(null);
  }, [session.scan_id, defaultMember]);

  const handleCancelVivaStream = () => {
    vivaAbortRef.current?.abort();
    vivaAbortRef.current = null;
    setVivaStream(null);
    setBusyAction(null);
  };

  const memberSlug = useMemo(() => {
    const matched = session.members.find((m) => m.name === selectedMember);
    return matched?.slug || slugifyMember(selectedMember);
  }, [session.members, selectedMember]);

  const loadProfile = useCallback(async (slug: string) => {
    setProfileLoading(true);
    try {
      const res = await getMemberProfile(slug);
      setProfile(res);
    } catch {
      setProfile({ member_slug: slug, concepts: [] });
    } finally {
      setProfileLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadProfile(memberSlug);
  }, [memberSlug, loadProfile]);

  const handleAsk = async () => {
    vivaAbortRef.current?.abort();
    const ctrl = new AbortController();
    vivaAbortRef.current = ctrl;

    setBusyAction("ask");
    setErrorMsg(null);
    setStatusMsg(null);
    setDefenseResult(null);
    setRevealAnswer(false);
    setSavedConfirmed(false);
    setVivaStream({
      action: "ask",
      stageLabel: "Giám khảo AI đang soạn câu hỏi vặn…",
      startedAt: Date.now(),
      reasoningText: "",
      contentText: "",
    });
    try {
      const res = await vivaAskStream(
        {
          scan_id: session.scan_id,
          member_name: selectedMember,
          topic: topic.trim() || undefined,
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
      setActiveCard({
        entryId: res.entry_id,
        mode: "ask",
        question: res.question,
        conceptKey: res.concept_key,
        term: res.term,
        tag: res.tag,
        sourceCite: res.source_cite,
        vivaMetaToken: res.viva_meta_token,
      });
      setAnswerText("");
    } catch (err) {
      setVivaStream(null);
      if ((err instanceof DOMException && err.name === "AbortError") || ctrl.signal.aborted) return;
      setErrorMsg(err instanceof Error ? err.message : "Không tạo được câu hỏi vặn.");
    } finally {
      if (vivaAbortRef.current === ctrl) {
        vivaAbortRef.current = null;
        setBusyAction(null);
      }
    }
  };

  const handleCoach = async () => {
    vivaAbortRef.current?.abort();
    const ctrl = new AbortController();
    vivaAbortRef.current = ctrl;

    setBusyAction("coach");
    setErrorMsg(null);
    setStatusMsg(null);
    setDefenseResult(null);
    setRevealAnswer(false);
    setSavedConfirmed(false);
    setVivaStream({
      action: "coach",
      stageLabel: "Đang phân tích điểm nghẽn để gợi mở +1 Bloom…",
      startedAt: Date.now(),
      reasoningText: "",
      contentText: "",
    });
    try {
      const res = await vivaCoachStream(
        {
          scan_id: session.scan_id,
          member_name: selectedMember,
          goal: topic.trim() || "Tư vấn lộ trình & nâng bậc +1 Bloom",
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
      setActiveCard({
        entryId: res.entry_id,
        mode: "coach",
        advice: res.advice,
        question: res.question,
        conceptKey: res.concept_key,
        term: res.term,
        tag: res.tag,
        sourceCite: res.source_cite,
        vivaMetaToken: res.viva_meta_token,
      });
      setAnswerText("");
    } catch (err) {
      setVivaStream(null);
      if ((err instanceof DOMException && err.name === "AbortError") || ctrl.signal.aborted) return;
      setErrorMsg(err instanceof Error ? err.message : "Không gọi được tư vấn nâng bậc Bloom.");
    } finally {
      if (vivaAbortRef.current === ctrl) {
        vivaAbortRef.current = null;
        setBusyAction(null);
      }
    }
  };

  const handleSubmitDefense = async (e: FormEvent) => {
    e.preventDefault();
    if (!activeCard || !answerText.trim()) return;
    vivaAbortRef.current?.abort();
    const ctrl = new AbortController();
    vivaAbortRef.current = ctrl;

    setBusyAction("defense");
    setErrorMsg(null);
    setStatusMsg(null);
    setSavedConfirmed(false);
    setVivaStream({
      action: "defense",
      stageLabel: "Giám khảo AI đang chấm mức hiểu Bloom L0–L6…",
      startedAt: Date.now(),
      reasoningText: "",
      contentText: "",
    });
    try {
      const res = await vivaDefenseStream(
        {
          scan_id: session.scan_id,
          member_name: selectedMember,
          question: activeCard.question,
          answer: answerText.trim(),
          viva_meta: activeCard.vivaMetaToken,
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
      setDefenseResult(res);
    } catch (err) {
      setVivaStream(null);
      if ((err instanceof DOMException && err.name === "AbortError") || ctrl.signal.aborted) return;
      setErrorMsg(err instanceof Error ? err.message : "Không đánh giá được câu trả lời.");
    } finally {
      if (vivaAbortRef.current === ctrl) {
        vivaAbortRef.current = null;
        setBusyAction(null);
      }
    }
  };

  const handleConfirmSave = async () => {
    if (!defenseResult) return;
    setBusyAction("confirm");
    setErrorMsg(null);
    try {
      const res = await confirmStudyLog({
        scan_id: session.scan_id,
        member_name: selectedMember,
        entry_id: defenseResult.entry_id,
        draft: defenseResult.draft ?? undefined,
      });
      setSavedConfirmed(true);
      setStatusMsg("Đã lưu chẩn đoán Bloom vào hồ sơ học tập của bạn.");
      if (res.profile) {
        setProfile(res.profile);
      } else {
        await loadProfile(memberSlug);
      }
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Lỗi khi xác nhận lưu hồ sơ.");
    } finally {
      setBusyAction(null);
    }
  };

  const handleCardStatus = async (conceptKey: string, status: CardStatus) => {
    setBusyAction(`status-${conceptKey}`);
    setErrorMsg(null);
    try {
      await updateCardStatus({
        scan_id: session.scan_id,
        member_name: selectedMember,
        concept_key: conceptKey,
        status,
      });
      setStatusMsg(
        status === "mastered"
          ? `Đã đánh dấu "${conceptKey}" là Đã hiểu.`
          : `Đã đưa "${conceptKey}" vào hàng đợi Chưa vững để ôn tiếp.`,
      );
      await loadProfile(memberSlug);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Không cập nhật được trạng thái thẻ.");
    } finally {
      setBusyAction(null);
    }
  };

  const handleDrillConcept = (concept: BloomConcept) => {
    setDefenseResult(null);
    setRevealAnswer(false);
    setSavedConfirmed(false);
    setAnswerText("");
    setActiveCard({
      mode: "queue",
      question:
        concept.next_probe ||
        concept.prompt ||
        `Hãy giải thích bằng lời của bạn cơ chế & bằng chứng cho khái niệm "${concept.term || concept.concept_key}".`,
      conceptKey: concept.concept_key,
      term: concept.term,
      tag: concept.tag,
      sourceCite: concept.source_cite,
      hiddenReference: concept.reference,
      hiddenRubric: concept.rubric,
    });
  };

  const handleRetry = () => {
    setAnswerText("");
    setDefenseResult(null);
    setRevealAnswer(false);
    setSavedConfirmed(false);
    setStatusMsg("Bạn có thể diễn đạt lại theo bản chất và nộp câu trả lời mới.");
  };

  const concepts = profile?.concepts ?? [];
  const weakQueue = concepts.filter((c) => c.status === "needs_review" || c.bloom_level <= 2);
  const masteredList = concepts.filter((c) => c.status === "mastered" && c.bloom_level >= 3);

  const currentDraft: BloomDraft | null | undefined = defenseResult?.draft;
  const currentConceptKey = currentDraft?.concept_key || activeCard?.conceptKey;
  const hiddenReferenceText = currentDraft?.reference || activeCard?.hiddenReference;
  const hiddenRubricText = currentDraft?.rubric || activeCard?.hiddenRubric;
  const hiddenCiteText = currentDraft?.source_cite || activeCard?.sourceCite;

  return (
    <div className="tabpanel-inner space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap items-end gap-3 border-b border-border pb-4">
        <div className="grid min-w-[210px] gap-1.5">
          {session.mode === "team" && session.members.length >= 2 ? (
            <>
              <label htmlFor="viva-member-select" className="text-xs font-medium text-muted-foreground">
                Bạn là ai trong team?
              </label>
              <select
                id="viva-member-select"
                className="h-9 rounded-md border border-input bg-background px-2.5 text-sm text-foreground focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-ring"
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
            </>
          ) : (
            <>
              <span className="text-xs font-medium text-muted-foreground">Hồ sơ cá nhân</span>
              <div className="flex h-9 items-center">
                <Badge>{selectedMember} (Cá nhân)</Badge>
              </div>
            </>
          )}
        </div>

        <div className="grid flex-1 min-w-[200px] gap-1.5">
          <label htmlFor="viva-topic-input" className="text-xs font-medium text-muted-foreground">
            Chủ đề (tùy chọn)
          </label>
          <Input
            id="viva-topic-input"
            name="topic"
            type="text"
            autoComplete="off"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="HAX G10, chống injection, số liệu…"
          />
        </div>

        <Button type="button" disabled={busyAction !== null} onClick={handleAsk}>
          <MessageSquare aria-hidden="true" className="h-3.5 w-3.5" />
          {busyAction === "ask" ? "Đang tạo…" : "Hỏi vặn"}
        </Button>

        <Button type="button" variant="secondary" disabled={busyAction !== null} onClick={handleCoach}>
          <TrendingUp aria-hidden="true" className="h-3.5 w-3.5" />
          {busyAction === "coach" ? "Đang phân tích…" : "Nâng +1 Bloom"}
        </Button>
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

      {/* Bloom L0-L6 strip (progressive disclosure) */}
      <details className="disclosure">
        <summary>Hồ sơ Bloom L0–L6 ({concepts.length} khái niệm)</summary>
        <div className="flex flex-wrap gap-1.5">
          {[0, 1, 2, 3, 4, 5, 6].map((lvl) => {
            const countAtLevel = concepts.filter((c) => c.bloom_level === lvl).length;
            const isActive = defenseResult?.bloom_level === lvl;
            return (
              <span
                key={lvl}
                title={BLOOM_LABELS[lvl]}
                className={cn(
                  "bloom-pill inline-flex items-center rounded border px-2 py-0.5 font-mono text-xs tabular-nums",
                  isActive
                    ? "is-active border-primary bg-primary text-primary-foreground font-semibold"
                    : "border-border bg-card text-foreground",
                )}
              >
                L{lvl} ({countAtLevel})
              </span>
            );
          })}
        </div>
      </details>

      {/* Main 2-column study grid */}
      <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,0.95fr)]">
        {/* Practice card */}
        <Card className="bg-card shadow-none" aria-label="Thẻ luyện phản biện Bloom">
          <CardContent className="p-4">
            {vivaStream ? (
              <div className="space-y-3" aria-live="polite">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="stream-dot shrink-0" aria-hidden="true" />
                    <strong className="text-sm text-foreground truncate">{vivaStream.stageLabel}</strong>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge variant="default" className="font-mono tabular-nums">
                      {vivaElapsedSec}s
                    </Badge>
                    <Button type="button" variant="outline" size="sm" onClick={handleCancelVivaStream}>
                      <X aria-hidden="true" className="h-3.5 w-3.5" />
                      Huỷ
                    </Button>
                  </div>
                </div>

                {vivaStream.reasoningText ? (
                  <details className="disclosure" open={!stripStreamingMeta(vivaStream.contentText)}>
                    <summary>
                      Suy luận của Giám khảo AI ({vivaStream.reasoningText.length.toLocaleString("vi-VN")} ký tự)
                    </summary>
                    <pre className="m-0 max-h-48 overflow-y-auto scroller whitespace-pre-wrap break-words rounded border border-border/70 bg-card/80 p-2.5 font-mono text-xs leading-relaxed text-muted-foreground">
                      {vivaStream.reasoningText}
                    </pre>
                  </details>
                ) : null}

                <div className="rounded-lg border border-border bg-muted/30 p-3.5">
                  {stripStreamingMeta(vivaStream.contentText) ? (
                    <MarkdownView text={stripStreamingMeta(vivaStream.contentText)} onSelectCite={onSelectCite} />
                  ) : (
                    <p className="m-0 text-sm text-muted-foreground">
                      {vivaStream.reasoningText
                        ? "Đang tổng hợp ý phản biện trước khi hiển thị…"
                        : "Đang chờ token phản hồi từ AI…"}
                    </p>
                  )}
                </div>
              </div>
            ) : !activeCard ? (
              <div className="space-y-1.5">
                <h2 className="m-0 text-base font-semibold text-foreground">Vấn đáp: {selectedMember}</h2>
                <p className="m-0 text-sm text-muted-foreground">
                  Chọn <strong>Hỏi vặn</strong>, <strong>Nâng +1 Bloom</strong> hoặc 1 thẻ ở{" "}
                  <strong>Hàng đợi yếu</strong>.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge>
                    {activeCard.mode === "coach"
                      ? "Gợi ý +1 Bloom"
                      : activeCard.mode === "queue"
                        ? "Thẻ yếu"
                        : "Hỏi vặn"}
                  </Badge>
                  {activeCard.tag ? <Badge variant="warning">{activeCard.tag}</Badge> : null}
                  {activeCard.term ? <strong className="text-sm">{activeCard.term}</strong> : null}
                </div>

                {activeCard.advice ? (
                  <details className="disclosure" open>
                    <summary>Gợi ý 3 tầng</summary>
                    <MarkdownView text={activeCard.advice} onSelectCite={onSelectCite} />
                  </details>
                ) : null}

                <div className="text-[15px] font-semibold leading-relaxed text-foreground">
                  <MarkdownView text={activeCard.question} onSelectCite={onSelectCite} />
                </div>

                {!defenseResult && !revealAnswer ? (
                  <div className="masked-hint rounded-md border border-dashed border-border bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
                    Đáp án được che trước khi nộp.
                  </div>
                ) : null}

                <form onSubmit={handleSubmitDefense} className="space-y-2.5">
                  <label htmlFor="viva-answer-box" className="block text-xs font-medium text-muted-foreground">
                    Câu trả lời
                  </label>
                  <Textarea
                    id="viva-answer-box"
                    name="answer"
                    value={answerText}
                    onChange={(e) => setAnswerText(e.target.value)}
                    placeholder="Nêu cơ chế và trích dẫn file:Lxx…"
                  />

                  <div className="flex flex-wrap items-center gap-2">
                    <Button type="submit" disabled={busyAction !== null || !answerText.trim()}>
                      {busyAction === "defense" ? "Đang chấm…" : "Nộp bài"}
                    </Button>

                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => setRevealAnswer((prev) => !prev)}
                    >
                      {revealAnswer ? (
                        <EyeOff aria-hidden="true" className="h-3.5 w-3.5" />
                      ) : (
                        <Eye aria-hidden="true" className="h-3.5 w-3.5" />
                      )}
                      {revealAnswer ? "Ẩn đáp án" : "Đáp án"}
                    </Button>

                    {defenseResult ? (
                      <Button type="button" variant="outline" onClick={handleRetry}>
                        <RotateCcw aria-hidden="true" className="h-3.5 w-3.5" />
                        Thử lại
                      </Button>
                    ) : null}
                  </div>
                </form>

                {revealAnswer && (hiddenReferenceText || hiddenRubricText || hiddenCiteText) ? (
                  <Alert variant="info" className="space-y-1.5 text-sm">
                    {hiddenCiteText ? (
                      <div>
                        <strong>Căn cứ:</strong> <CiteText text={hiddenCiteText} onSelectCite={onSelectCite} />
                      </div>
                    ) : null}
                    {hiddenReferenceText ? (
                      <div>
                        <strong>Điểm chốt:</strong>{" "}
                        <InlineMarkdown text={hiddenReferenceText} onSelectCite={onSelectCite} />
                      </div>
                    ) : null}
                    {hiddenRubricText ? (
                      <div>
                        <strong>Tiêu chí đạt:</strong>{" "}
                        <InlineMarkdown text={hiddenRubricText} onSelectCite={onSelectCite} />
                      </div>
                    ) : null}
                  </Alert>
                ) : null}

                {/* 4-section Bloom feedback */}
                {defenseResult ? (
                  <div
                    className="feedback-box rounded-lg border border-border border-l-4 border-l-primary bg-card p-3.5 space-y-3"
                    role="region"
                    aria-label="Chẩn đoán Bloom 4 mục"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <strong className="text-sm">Chẩn đoán Bloom</strong>
                      {typeof defenseResult.bloom_level === "number" ? (
                        <div className="flex flex-wrap items-center gap-1.5">
                          <Badge>Level {defenseResult.bloom_level}/6</Badge>
                          <span className="text-xs text-muted-foreground">
                            {defenseResult.bloom_label || BLOOM_LABELS[defenseResult.bloom_level]}
                          </span>
                        </div>
                      ) : null}
                    </div>

                    <MarkdownView text={defenseResult.ai_feedback} onSelectCite={onSelectCite} />

                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      <Button
                        type="button"
                        variant="teal"
                        disabled={busyAction !== null || savedConfirmed}
                        onClick={handleConfirmSave}
                      >
                        <BookmarkCheck aria-hidden="true" className="h-3.5 w-3.5" />
                        {savedConfirmed ? "Đã lưu" : busyAction === "confirm" ? "Đang lưu…" : "Lưu hồ sơ"}
                      </Button>

                      {currentConceptKey ? (
                        <>
                          <Button
                            type="button"
                            variant="destructive"
                            size="sm"
                            disabled={busyAction !== null}
                            onClick={() => handleCardStatus(currentConceptKey, "needs_review")}
                          >
                            Chưa vững
                          </Button>
                          <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            disabled={busyAction !== null}
                            onClick={() => handleCardStatus(currentConceptKey, "mastered")}
                          >
                            <Check aria-hidden="true" className="h-3.5 w-3.5" />
                            Đã hiểu
                          </Button>
                        </>
                      ) : null}
                    </div>
                  </div>
                ) : null}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right column: Weak queue */}
        <aside aria-label="Hàng đợi yếu">
          <Card className="bg-card shadow-none">
            <CardHeader className="flex-row items-center justify-between gap-2 p-4 pb-2">
              <CardTitle className="text-sm font-semibold">Hàng đợi yếu ({weakQueue.length})</CardTitle>
              <Badge variant="success">Vững: {masteredList.length}</Badge>
            </CardHeader>
            <CardContent className="p-4 pt-2">
              {profileLoading ? (
                <p className="m-0 text-xs text-muted-foreground">Đang tải…</p>
              ) : concepts.length === 0 ? (
                <p className="m-0 text-xs text-muted-foreground">
                  Chưa có thẻ của <strong>{selectedMember}</strong>.
                </p>
              ) : (
                <ul className="m-0 grid list-none gap-2.5 p-0">
                  {(weakQueue.length > 0 ? weakQueue : concepts).map((c) => (
                    <li key={c.concept_key} className="rounded-md border border-border bg-card p-3 space-y-2">
                      <div className="flex items-center justify-between gap-2">
                        <strong className="text-sm leading-snug">{c.term || c.concept_key}</strong>
                        <Badge
                          variant={
                            c.bloom_level <= 1 ? "destructive" : c.bloom_level <= 3 ? "warning" : "success"
                          }
                        >
                          L{c.bloom_level}/6
                        </Badge>
                      </div>

                      {c.source_cite ? (
                        <div className="text-xs">
                          <CiteText text={c.source_cite} onSelectCite={onSelectCite} />
                        </div>
                      ) : null}

                      {c.misconceptions && c.misconceptions.length > 0 ? (
                        <p className="m-0 text-xs text-destructive">{c.misconceptions[0]}</p>
                      ) : null}

                      <div className="flex flex-wrap gap-1.5">
                        <Button
                          type="button"
                          variant="secondary"
                          size="sm"
                          onClick={() => handleDrillConcept(c)}
                        >
                          Ôn lại
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            handleCardStatus(
                              c.concept_key,
                              c.status === "mastered" ? "needs_review" : "mastered",
                            )
                          }
                        >
                          {c.status === "mastered" ? "Chưa vững" : "Đã hiểu"}
                        </Button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}
