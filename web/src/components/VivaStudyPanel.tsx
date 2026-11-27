import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import {
  confirmStudyLog,
  getMemberProfile,
  updateCardStatus,
  vivaAsk,
  vivaCoach,
  vivaDefense,
} from "../api/client.ts";
import type {
  BloomConcept,
  BloomDraft,
  CardStatus,
  MemberProfileResponse,
  ScanSessionDetail,
  VivaDefenseResponse,
} from "../types.ts";
import { BLOOM_LABELS, slugifyMember } from "../utils/citations.ts";
import { CiteText } from "./CiteText.tsx";

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
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    setSelectedMember(defaultMember);
    setActiveCard(null);
    setDefenseResult(null);
    setAnswerText("");
    setRevealAnswer(false);
    setSavedConfirmed(false);
    setErrorMsg(null);
    setStatusMsg(null);
  }, [session.scan_id, defaultMember]);

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
    setBusyAction("ask");
    setErrorMsg(null);
    setStatusMsg(null);
    setDefenseResult(null);
    setRevealAnswer(false);
    setSavedConfirmed(false);
    try {
      const res = await vivaAsk({
        scan_id: session.scan_id,
        member_name: selectedMember,
        topic: topic.trim() || undefined,
      });
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
      setErrorMsg(err instanceof Error ? err.message : "Không tạo được câu hỏi vặn.");
    } finally {
      setBusyAction(null);
    }
  };

  const handleCoach = async () => {
    setBusyAction("coach");
    setErrorMsg(null);
    setStatusMsg(null);
    setDefenseResult(null);
    setRevealAnswer(false);
    setSavedConfirmed(false);
    try {
      const res = await vivaCoach({
        scan_id: session.scan_id,
        member_name: selectedMember,
        goal: topic.trim() || "Tư vấn lộ trình & nâng bậc +1 Bloom",
      });
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
      setErrorMsg(err instanceof Error ? err.message : "Không gọi được tư vấn nâng bậc Bloom.");
    } finally {
      setBusyAction(null);
    }
  };

  const handleSubmitDefense = async (e: FormEvent) => {
    e.preventDefault();
    if (!activeCard || !answerText.trim()) return;
    setBusyAction("defense");
    setErrorMsg(null);
    setStatusMsg(null);
    setSavedConfirmed(false);
    try {
      const res = await vivaDefense({
        scan_id: session.scan_id,
        member_name: selectedMember,
        question: activeCard.question,
        answer: answerText.trim(),
        viva_meta: activeCard.vivaMetaToken,
      });
      setDefenseResult(res);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Không đánh giá được câu trả lời.");
    } finally {
      setBusyAction(null);
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
    <div className="tabpanel-inner">
      {/* Chon danh tinh + Nut Hỏi vặn / Tư vấn Bloom */}
      <div className="viva-toolbar">
        <div className="field-group" style={{ minWidth: "220px" }}>
          {session.mode === "team" && session.members.length >= 2 ? (
            <>
              <label htmlFor="viva-member-select" className="field-label">
                Bạn là ai trong team?
              </label>
              <select
                id="viva-member-select"
                className="select-input"
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
              <span className="field-label">Hồ sơ cá nhân</span>
              <div className="stamp stamp-navy">
                {selectedMember} (Mặc định cá nhân)
              </div>
            </>
          )}
        </div>

        <div className="field-group" style={{ flex: "1 1 220px" }}>
          <label htmlFor="viva-topic-input" className="field-label">
            Chủ đề muốn xoáy sâu (tùy chọn)
          </label>
          <input
            id="viva-topic-input"
            name="topic"
            type="text"
            autoComplete="off"
            className="text-input"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="HAX G10, chống injection, số liệu…"
          />
        </div>

        <button
          type="button"
          className="btn btn-primary"
          disabled={busyAction !== null}
          onClick={handleAsk}
        >
          {busyAction === "ask" ? "Đang tạo…" : "Hỏi vặn"}
        </button>

        <button
          type="button"
          className="btn btn-secondary"
          disabled={busyAction !== null}
          onClick={handleCoach}
        >
          {busyAction === "coach" ? "Đang phân tích…" : "Nâng +1 Bloom"}
        </button>
      </div>

      {errorMsg && (
        <div className="alert alert-error" role="alert">
          {errorMsg}
        </div>
      )}
      {statusMsg && (
        <div className="alert alert-ok" role="status" aria-live="polite">
          {statusMsg}
        </div>
      )}

      {/* Thanh ho so Bloom L0-L6 (progressive disclosure) */}
      <details className="disclosure">
        <summary>Hồ sơ Bloom L0–L6 ({concepts.length} khái niệm)</summary>
        <div className="bloom-strip" style={{ marginBottom: 0 }}>
          {[0, 1, 2, 3, 4, 5, 6].map((lvl) => {
            const countAtLevel = concepts.filter((c) => c.bloom_level === lvl).length;
            const isActive = defenseResult?.bloom_level === lvl;
            return (
              <span
                key={lvl}
                className={`bloom-pill${isActive ? " is-active" : ""}`}
                title={BLOOM_LABELS[lvl]}
              >
                L{lvl} ({countAtLevel})
              </span>
            );
          })}
        </div>
      </details>

      <div className="viva-grid">
        {/* Cot trai: The luyen tap che dap an kieu _etude */}
        <section className="study-card" aria-label="Thẻ luyện phản biện Bloom">
          {!activeCard ? (
            <div>
              <h2 style={{ marginTop: 0, fontSize: "1.05rem" }}>Vấn đáp: {selectedMember}</h2>
              <p style={{ color: "var(--ink-muted)", marginBottom: 0 }}>
                Chọn <strong>Hỏi vặn</strong>, <strong>Nâng +1 Bloom</strong> hoặc 1 thẻ ở <strong>Hàng đợi yếu</strong>.
              </p>
            </div>
          ) : (
            <>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.45rem", alignItems: "center", marginBottom: "0.65rem" }}>
                <span className="stamp stamp-navy">
                  {activeCard.mode === "coach"
                    ? "Gợi ý +1 Bloom"
                    : activeCard.mode === "queue"
                      ? "Thẻ yếu"
                      : "Hỏi vặn"}
                </span>
                {activeCard.tag ? <span className="stamp stamp-warn">{activeCard.tag}</span> : null}
                {activeCard.term ? <strong>{activeCard.term}</strong> : null}
              </div>

              {activeCard.advice ? (
                <details className="disclosure" open>
                  <summary>Gợi ý 3 tầng</summary>
                  <div style={{ whiteSpace: "pre-wrap", fontSize: "0.9rem" }}>
                    <CiteText text={activeCard.advice} onSelectCite={onSelectCite} />
                  </div>
                </details>
              ) : null}

              <div style={{ fontSize: "1.02rem", fontWeight: 600, marginBottom: "0.65rem", whiteSpace: "pre-wrap" }}>
                <CiteText text={activeCard.question} onSelectCite={onSelectCite} />
              </div>

              {!defenseResult && !revealAnswer ? (
                <div className="masked-hint">Đáp án được che trước khi nộp.</div>
              ) : null}

              <form onSubmit={handleSubmitDefense}>
                <label htmlFor="viva-answer-box" className="field-label" style={{ display: "block", marginBottom: "0.35rem" }}>
                  Câu trả lời
                </label>
                <textarea
                  id="viva-answer-box"
                  name="answer"
                  className="textarea-input"
                  value={answerText}
                  onChange={(e) => setAnswerText(e.target.value)}
                  placeholder="Nêu cơ chế và trích dẫn file:Lxx…"
                />

                <div className="action-row">
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={busyAction !== null || !answerText.trim()}
                  >
                    {busyAction === "defense" ? "Đang chấm…" : "Nộp bài"}
                  </button>

                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => setRevealAnswer((prev) => !prev)}
                  >
                    {revealAnswer ? "Ẩn đáp án" : "Đáp án"}
                  </button>

                  {defenseResult ? (
                    <button type="button" className="btn btn-secondary" onClick={handleRetry}>
                      Thử lại
                    </button>
                  ) : null}
                </div>
              </form>

              {revealAnswer && (hiddenReferenceText || hiddenRubricText || hiddenCiteText) ? (
                <div className="alert alert-info" style={{ marginTop: "0.85rem" }}>
                  {hiddenCiteText ? (
                    <div>
                      <strong>Căn cứ:</strong> <CiteText text={hiddenCiteText} onSelectCite={onSelectCite} />
                    </div>
                  ) : null}
                  {hiddenReferenceText ? (
                    <div style={{ marginTop: "0.35rem", whiteSpace: "pre-wrap" }}>
                      <strong>Bản chất / Điểm chốt:</strong>{" "}
                      <CiteText text={hiddenReferenceText} onSelectCite={onSelectCite} />
                    </div>
                  ) : null}
                  {hiddenRubricText ? (
                    <div style={{ marginTop: "0.35rem", whiteSpace: "pre-wrap" }}>
                      <strong>Tiêu chí đạt:</strong>{" "}
                      <CiteText text={hiddenRubricText} onSelectCite={onSelectCite} />
                    </div>
                  ) : null}
                </div>
              ) : null}

              {/* Khung phan hoi Bloom 4 muc */}
              {defenseResult ? (
                <div className="feedback-box" role="region" aria-label="Chẩn đoán Bloom 4 mục">
                  <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: "0.5rem", marginBottom: "0.6rem" }}>
                    <strong>Phản hồi chẩn đoán Bloom</strong>
                    {typeof defenseResult.bloom_level === "number" ? (
                      <span className="stamp stamp-navy">
                        Level {defenseResult.bloom_level}/6 — {defenseResult.bloom_label || BLOOM_LABELS[defenseResult.bloom_level]}
                      </span>
                    ) : null}
                  </div>

                  <div style={{ whiteSpace: "pre-wrap", fontSize: "0.93rem" }}>
                    <CiteText text={defenseResult.ai_feedback} onSelectCite={onSelectCite} />
                  </div>

                  <div className="action-row">
                    <button
                      type="button"
                      className="btn btn-teal"
                      disabled={busyAction !== null || savedConfirmed}
                      onClick={handleConfirmSave}
                    >
                      {savedConfirmed
                        ? "Đã lưu"
                        : busyAction === "confirm"
                          ? "Đang lưu…"
                          : "Lưu hồ sơ"}
                    </button>

                    {currentConceptKey ? (
                      <>
                        <button
                          type="button"
                          className="btn btn-crimson"
                          disabled={busyAction !== null}
                          onClick={() => handleCardStatus(currentConceptKey, "needs_review")}
                        >
                          Chưa vững
                        </button>
                        <button
                          type="button"
                          className="btn btn-secondary"
                          disabled={busyAction !== null}
                          onClick={() => handleCardStatus(currentConceptKey, "mastered")}
                        >
                          Đã hiểu
                        </button>
                      </>
                    ) : null}
                  </div>
                </div>
              ) : null}
            </>
          )}
        </section>

        {/* Cot phai: Hang doi the yeu & Ho so Bloom xuyen suot */}
        <aside className="study-card" aria-label="Hàng đợi yếu">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
            <h2 style={{ margin: 0, fontSize: "1rem" }}>Hàng đợi yếu ({weakQueue.length})</h2>
            <span className="stamp stamp-teal">Vững: {masteredList.length}</span>
          </div>

          {profileLoading ? (
            <p style={{ color: "var(--ink-muted)", fontSize: "0.88rem" }}>Đang tải…</p>
          ) : concepts.length === 0 ? (
            <p style={{ color: "var(--ink-muted)", fontSize: "0.88rem", marginBottom: 0 }}>
              Chưa có thẻ của <strong>{selectedMember}</strong>.
            </p>
          ) : (
            <ul className="queue-list">
              {(weakQueue.length > 0 ? weakQueue : concepts).map((c) => (
                <li key={c.concept_key} className="queue-item">
                  <div style={{ display: "flex", justifyContent: "space-between", gap: "0.4rem", alignItems: "center" }}>
                    <strong>{c.term || c.concept_key}</strong>
                    <span className={`stamp ${c.bloom_level <= 1 ? "stamp-crimson" : c.bloom_level <= 3 ? "stamp-warn" : "stamp-teal"}`}>
                      L{c.bloom_level}/6
                    </span>
                  </div>

                  {c.source_cite ? (
                    <div style={{ fontSize: "0.8rem", marginTop: "0.25rem" }}>
                      <CiteText text={c.source_cite} onSelectCite={onSelectCite} />
                    </div>
                  ) : null}

                  {c.misconceptions && c.misconceptions.length > 0 ? (
                    <p style={{ fontSize: "0.82rem", color: "var(--stamp-crimson)", margin: "0.35rem 0 0" }}>
                      {c.misconceptions[0]}
                    </p>
                  ) : null}

                  <div className="action-row" style={{ marginTop: "0.55rem" }}>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{ padding: "0.3rem 0.65rem", fontSize: "0.8rem" }}
                      onClick={() => handleDrillConcept(c)}
                    >
                      Ôn lại
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{ padding: "0.3rem 0.65rem", fontSize: "0.8rem" }}
                      onClick={() =>
                        handleCardStatus(
                          c.concept_key,
                          c.status === "mastered" ? "needs_review" : "mastered",
                        )
                      }
                    >
                      {c.status === "mastered" ? "Chưa vững" : "Đã hiểu"}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </aside>
      </div>
    </div>
  );
}
