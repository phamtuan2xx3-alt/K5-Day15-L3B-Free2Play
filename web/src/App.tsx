import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState, type KeyboardEvent } from "react";
import { BookMarked, FileSearch, MessageSquare, type LucideIcon } from "lucide-react";
import {
  ApiError,
  getFileLines,
  getMe,
  getSession,
  getSessionDiff,
  getSubmissions,
  listSessions,
  scanTargetStream,
} from "@/api/client.ts";
import { AuditPanel, ScanStreamPanel } from "@/components/AuditPanel.tsx";
import { CiteDialog } from "@/components/CiteDialog.tsx";
import { KnowledgeHubPanel } from "@/components/KnowledgeHubPanel.tsx";
import { LegalPage } from "@/components/LegalPages.tsx";
import { ScanSidebar } from "@/components/ScanSidebar.tsx";
import { TopBar } from "@/components/TopBar.tsx";
import { VivaStudyPanel } from "@/components/VivaStudyPanel.tsx";
import { Alert } from "@/components/ui/alert.tsx";
import { Button } from "@/components/ui/button.tsx";
import type {
  BloomConcept,
  FileLineItem,
  MeResponse,
  ScanDiffSummary,
  ScanSessionDetail,
  ScanSessionSummary,
  ScanStreamState,
  SubmissionOption,
} from "@/types.ts";
import { parseAuditReport, type VivaStarterQuestion } from "@/utils/auditSections.ts";
import { extractUrlHackTarget } from "@/utils/citations.ts";

type TabId = "audit" | "viva" | "knowledge";

const TABS: Array<{ id: TabId; label: string; icon: LucideIcon }> = [
  { id: "audit", label: "Soi Repo", icon: FileSearch },
  { id: "viva", label: "Vấn đáp", icon: MessageSquare },
  { id: "knowledge", label: "Hệ thống kiến thức", icon: BookMarked },
];

export function App() {
  const [pathname, setPathname] = useState<string>(() => window.location.pathname);
  const [me, setMe] = useState<MeResponse | null>(null);
  const [submissions, setSubmissions] = useState<SubmissionOption[]>([]);
  const [sessions, setSessions] = useState<ScanSessionSummary[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);

  const [targetInput, setTargetInput] = useState<string>("");
  const [activeSession, setActiveSession] = useState<ScanSessionDetail | null>(null);
  const [activeDiff, setActiveDiff] = useState<ScanDiffSummary | null>(null);
  const [scanning, setScanning] = useState(false);
  const [scanStream, setScanStream] = useState<ScanStreamState | null>(null);
  const scanAbortRef = useRef<AbortController | null>(null);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [needsAuth, setNeedsAuth] = useState(false);

  const [activeTab, setActiveTab] = useState<TabId>("audit");
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem("repoksv-sidebar-collapsed") === "1";
    } catch {
      return false;
    }
  });
  const [vivaStarters, setVivaStarters] = useState<VivaStarterQuestion[]>([]);
  const [drillConcept, setDrillConcept] = useState<BloomConcept | null>(null);
  const [knowledgeVersion, setKnowledgeVersion] = useState<number>(0);
  const baseId = useId();
  const tabRefs = useRef<Record<TabId, HTMLButtonElement | null>>({
    audit: null,
    viva: null,
    knowledge: null,
  });
  const panelRefs = useRef<Record<TabId, HTMLDivElement | null>>({
    audit: null,
    viva: null,
    knowledge: null,
  });

  // Cite Modal state
  const [citeState, setCiteState] = useState<{
    open: boolean;
    file: string;
    line: number;
    lines: FileLineItem[];
    loading: boolean;
    error: string | null;
  }>({
    open: false,
    file: "",
    line: 1,
    lines: [],
    loading: false,
    error: null,
  });

  const navigate = useCallback((nextPath: string) => {
    if (window.location.pathname !== nextPath) {
      window.history.pushState(null, "", nextPath);
      setPathname(nextPath);
    }
  }, []);

  useEffect(() => {
    const onPop = () => setPathname(window.location.pathname);
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const refreshSessions = useCallback(async () => {
    setSessionsLoading(true);
    try {
      const list = await listSessions();
      setSessions(list);
      return list;
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setNeedsAuth(true);
      }
      return [];
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  const handleSelectSession = useCallback(async (scanId: string) => {
    setGlobalError(null);
    try {
      const detail = await getSession(scanId);
      setActiveSession(detail);
      setActiveDiff(detail.diff ?? null);
      setVivaStarters(parseAuditReport(detail.audit_output).vivaQuestions);
      if (!detail.diff) {
        getSessionDiff(scanId)
          .then((d) => setActiveDiff(d))
          .catch(() => {});
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setNeedsAuth(true);
      } else {
        setGlobalError(err instanceof Error ? err.message : "Không tải được chi tiết phiên.");
      }
    }
  }, []);

  const handleCancelScan = useCallback(() => {
    scanAbortRef.current?.abort();
    scanAbortRef.current = null;
    setScanStream(null);
    setScanning(false);
  }, []);

  const handleScan = useCallback(
    async (target: string, forceRefresh = false) => {
      scanAbortRef.current?.abort();
      const ctrl = new AbortController();
      scanAbortRef.current = ctrl;

      setScanning(true);
      setGlobalError(null);
      setNeedsAuth(false);
      setActiveTab("audit");
      setScanStream({
        target,
        stageStep: "fetch",
        stageLabel: `Đang khởi tạo quét ${target}…`,
        startedAt: Date.now(),
        preflight: null,
        reasoningText: "",
        contentText: "",
      });

      try {
        const detail = await scanTargetStream(target, forceRefresh, {
          signal: ctrl.signal,
          onStage: (ev) => {
            setScanStream((prev) =>
              prev ? { ...prev, stageStep: ev.step || prev.stageStep, stageLabel: ev.label || prev.stageLabel } : prev,
            );
          },
          onPreflight: (preflight) => {
            setScanStream((prev) => (prev ? { ...prev, preflight } : prev));
          },
          onReasoning: (delta) => {
            setScanStream((prev) => (prev ? { ...prev, reasoningText: prev.reasoningText + delta } : prev));
          },
          onContent: (delta) => {
            setScanStream((prev) => (prev ? { ...prev, contentText: prev.contentText + delta } : prev));
          },
        });
        if (ctrl.signal.aborted) return;
        setActiveSession(detail);
        setActiveDiff(detail.diff ?? null);
        setVivaStarters(parseAuditReport(detail.audit_output).vivaQuestions);
        setActiveTab("audit");
        setScanStream(null);
        await refreshSessions();
      } catch (err) {
        if ((err instanceof DOMException && err.name === "AbortError") || ctrl.signal.aborted) {
          return;
        }
        setScanStream(null);
        if (err instanceof ApiError && err.status === 401) {
          setNeedsAuth(true);
          setGlobalError(err.message);
        } else {
          setGlobalError(err instanceof Error ? err.message : "Quét hồ sơ thất bại.");
        }
      } finally {
        if (scanAbortRef.current === ctrl) {
          scanAbortRef.current = null;
          setScanning(false);
        }
      }
    },
    [refreshSessions],
  );

  useEffect(() => {
    let cancelled = false;

    async function boot() {
      const [meRes, subsRes] = await Promise.all([
        getMe().catch(() => ({ authenticated: false, user: null, guest_demo: false })),
        getSubmissions().catch(() => []),
      ]);
      if (cancelled) return;

      setMe(meRes);
      setSubmissions(subsRes);

      if (!meRes.authenticated && !meRes.guest_demo) {
        setNeedsAuth(true);
        setSessionsLoading(false);
        return;
      }

      const urlHack = extractUrlHackTarget(window.location.pathname);
      if (urlHack) {
        setTargetInput(urlHack);
        await handleScan(urlHack, false);
        return;
      }

      const list = await refreshSessions();
      if (!cancelled && list.length > 0) {
        await handleSelectSession(list[0].scan_id);
      }
    }

    void boot();
    return () => {
      cancelled = true;
    };
  }, [handleScan, handleSelectSession, refreshSessions]);

  // Sync hidden="until-found" synchronously before paint to eliminate tab-switch flicker
  useLayoutEffect(() => {
    for (const tab of TABS) {
      const panel = panelRefs.current[tab.id];
      if (!panel) continue;
      if (tab.id === activeTab) {
        panel.removeAttribute("hidden");
      } else {
        panel.setAttribute("hidden", "until-found");
      }
    }
  }, [activeTab, activeSession]);

  useEffect(() => {
    const cleanups: Array<() => void> = [];
    for (const tab of TABS) {
      const panel = panelRefs.current[tab.id];
      if (!panel) continue;
      const onBeforeMatch = () => {
        setActiveTab(tab.id);
      };
      panel.addEventListener("beforematch", onBeforeMatch);
      cleanups.push(() => panel.removeEventListener("beforematch", onBeforeMatch));
    }
    return () => {
      for (const fn of cleanups) fn();
    };
  }, [activeSession]);

  const selectTab = (tabId: TabId) => {
    setActiveTab(tabId);
  };

  const handleTabKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    const idx = TABS.findIndex((t) => t.id === activeTab);
    let nextIdx = -1;
    if (e.key === "ArrowRight") nextIdx = (idx + 1) % TABS.length;
    else if (e.key === "ArrowLeft") nextIdx = (idx - 1 + TABS.length) % TABS.length;
    else if (e.key === "Home") nextIdx = 0;
    else if (e.key === "End") nextIdx = TABS.length - 1;

    if (nextIdx >= 0) {
      e.preventDefault();
      const nextTab = TABS[nextIdx].id;
      selectTab(nextTab);
      const btn = tabRefs.current[nextTab];
      btn?.focus();
      const listEl = e.currentTarget;
      if (btn && listEl.scrollWidth > listEl.clientWidth) {
        btn.scrollIntoView({ block: "nearest", inline: "nearest" });
      }
    }
  };

  const handleOpenCite = useCallback(
    async (file: string, line: number, overrideScanId?: string) => {
      const targetScanId = overrideScanId || activeSession?.scan_id;
      if (!targetScanId) return;
      setCiteState({
        open: true,
        file,
        line,
        lines: [],
        loading: true,
        error: null,
      });
      try {
        const res = await getFileLines(targetScanId, file, line);
        setCiteState((prev) =>
          prev.open
            ? {
                ...prev,
                file: res.file,
                line: res.target_line ?? line,
                lines: res.lines,
                loading: false,
                error: null,
              }
            : prev,
        );
      } catch (err) {
        setCiteState((prev) => ({
          ...prev,
          loading: false,
          error: err instanceof Error ? err.message : "Không tải được dòng nguồn.",
        }));
      }
    },
    [activeSession],
  );

  const handleDrillFromKnowledge = useCallback(
    async (concept: BloomConcept) => {
      setDrillConcept(concept);
      const targetScanId = concept.source_scan_id;
      if (targetScanId && targetScanId !== activeSession?.scan_id) {
        await handleSelectSession(targetScanId);
      } else if (
        !targetScanId &&
        concept.source_repo &&
        concept.source_repo !== activeSession?.source_label
      ) {
        const matched = sessions.find((s) => s.source_label === concept.source_repo);
        if (matched) {
          await handleSelectSession(matched.scan_id);
        }
      }
      selectTab("viva");
    },
    [activeSession?.scan_id, activeSession?.source_label, handleSelectSession, sessions],
  );

  const toggleSidebarCollapsed = useCallback(() => {
    setSidebarCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem("repoksv-sidebar-collapsed", next ? "1" : "0");
      } catch {
        // ignore storage errors
      }
      return next;
    });
  }, []);

  const isLegalRoute = pathname === "/login" || pathname === "/privacy" || pathname === "/terms";

  const footerNode = (
    <footer className="border-t border-border bg-card/60 px-4 py-3 text-xs text-muted-foreground sm:px-6">
      <div className="mx-auto flex w-full max-w-[1040px] flex-wrap items-center justify-between gap-3">
        <span>RepoKSV · Giám khảo ảo AI20K (Nhóm Free2Play · NO-AUTO-GRADE)</span>
        <nav aria-label="Liên kết pháp lý">
          <ul className="m-0 flex list-none gap-4 p-0">
            <li>
              <a
                href="/privacy"
                className="text-primary hover:underline"
                onClick={(e) => {
                  e.preventDefault();
                  navigate("/privacy");
                }}
              >
                Quyền riêng tư
              </a>
            </li>
            <li>
              <a
                href="/terms"
                className="text-primary hover:underline"
                onClick={(e) => {
                  e.preventDefault();
                  navigate("/terms");
                }}
              >
                Điều khoản
              </a>
            </li>
            <li>
              <a
                href="/login"
                className="text-primary hover:underline"
                onClick={(e) => {
                  e.preventDefault();
                  navigate("/login");
                }}
              >
                Đăng nhập
              </a>
            </li>
          </ul>
        </nav>
      </div>
    </footer>
  );

  return (
    <div
      className={
        isLegalRoute
          ? "flex min-h-screen flex-col bg-background text-foreground"
          : "flex min-h-screen flex-col bg-background text-foreground lg:h-screen lg:overflow-hidden"
      }
    >
      {isLegalRoute ? (
        <>
          <TopBar
            targetInput={targetInput}
            onTargetInputChange={setTargetInput}
            submissions={submissions}
            scanning={scanning}
            showBrandOnDesktop
            onScan={(t, force) => {
              navigate("/");
              void handleScan(t, force);
            }}
            onNavigate={navigate}
          />
          <LegalPage route={pathname as "/login" | "/privacy" | "/terms"} onNavigate={navigate} />
          {footerNode}
        </>
      ) : (
        <div
          className={
            sidebarCollapsed
              ? "grid flex-1 grid-cols-1 lg:min-h-0 lg:overflow-hidden lg:grid-cols-[64px_minmax(0,1fr)] lg:transition-[grid-template-columns] lg:duration-250 lg:ease-[cubic-bezier(0.23,1,0.32,1)]"
              : "grid flex-1 grid-cols-1 lg:min-h-0 lg:overflow-hidden lg:grid-cols-[260px_minmax(0,1fr)] lg:transition-[grid-template-columns] lg:duration-250 lg:ease-[cubic-bezier(0.23,1,0.32,1)]"
          }
        >
          <ScanSidebar
            sessions={sessions}
            activeScanId={activeSession?.scan_id ?? null}
            onSelectSession={(id) => void handleSelectSession(id)}
            loading={sessionsLoading}
            me={me}
            onNavigate={navigate}
            collapsed={sidebarCollapsed}
            onToggleCollapse={toggleSidebarCollapsed}
          />

          <div className="order-first lg:order-last flex min-w-0 flex-col bg-background lg:min-h-0 lg:overflow-hidden">
            <TopBar
              targetInput={targetInput}
              onTargetInputChange={setTargetInput}
              submissions={submissions}
              scanning={scanning}
              onScan={(t, force) => void handleScan(t, force)}
              onNavigate={navigate}
            />

            <div
              id="content-scroller"
              className="scroller flex flex-1 flex-col lg:min-h-0 lg:overflow-y-auto [scrollbar-gutter:stable]"
            >
            <main
              id="main-content"
              tabIndex={-1}
              className="flex-1 min-w-0"
              aria-label="Bảng kiểm toán và luyện phản biện"
            >
              {globalError && (
                <Alert variant="destructive" role="alert" className="mx-4 mt-4 w-auto sm:mx-6">
                  {globalError}
                </Alert>
              )}

              {needsAuth ? (
                <div className="tabpanel-inner mx-auto w-full max-w-[1040px] space-y-3">
                  <h1 className="m-0 text-xl font-bold tracking-tight">Đăng nhập để quét &amp; lưu hồ sơ Bloom</h1>
                  <p className="m-0 text-sm text-muted-foreground">
                    Máy chủ hiện yêu cầu tài khoản Google.
                  </p>
                  <a
                    href="/auth/google"
                    className="inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground no-underline hover:bg-primary/90"
                  >
                    Đăng nhập Google
                  </a>
                </div>
              ) : scanStream ? (
                <ScanStreamPanel stream={scanStream} onCancel={handleCancelScan} />
              ) : !activeSession ? (
                <div className="tabpanel-inner mx-auto w-full max-w-[1040px] space-y-3">
                  <h1 className="m-0 text-xl font-bold tracking-tight">
                    {scanning ? "Đang quét…" : "Chọn S01–S30 hoặc dán link GitHub"}
                  </h1>
                  {submissions.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {submissions.slice(0, 4).map((sub) => (
                        <Button
                          key={sub.id}
                          type="button"
                          variant="secondary"
                          disabled={scanning}
                          onClick={() => {
                            setTargetInput(sub.id);
                            void handleScan(sub.id, false);
                          }}
                        >
                          Thử {sub.id}
                        </Button>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <>
                  <h1 className="sr-only">Kiểm toán và Vấn đáp: {activeSession.source_label}</h1>
                  <div className="border-b border-border bg-card/50">
                    <div className="mx-auto flex w-full max-w-[1040px] items-center px-4 py-2.5 sm:px-6">
                      <div
                        role="tablist"
                        aria-label="Khu vực làm việc RepoKSV"
                        className="inline-flex max-w-full overflow-x-auto items-center gap-1 rounded-lg border border-border bg-muted/70 p-1"
                        onKeyDown={handleTabKeyDown}
                      >
                        {TABS.map((tab) => {
                          const selected = activeTab === tab.id;
                          const Icon = tab.icon;
                          return (
                            <button
                              key={tab.id}
                              ref={(el) => {
                                tabRefs.current[tab.id] = el;
                              }}
                              type="button"
                              role="tab"
                              id={`${baseId}-tab-${tab.id}`}
                              aria-controls={`${baseId}-panel-${tab.id}`}
                              aria-selected={selected}
                              tabIndex={selected ? 0 : -1}
                              className="tab-btn"
                              onClick={() => selectTab(tab.id)}
                            >
                              <Icon aria-hidden="true" className="h-[15px] w-[15px] shrink-0" />
                              <span>{tab.label}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>

                  <div
                    ref={(el) => {
                      panelRefs.current.audit = el;
                    }}
                    role="tabpanel"
                    id={`${baseId}-panel-audit`}
                    aria-labelledby={`${baseId}-tab-audit`}
                    className="tabpanel"
                  >
                    <AuditPanel
                      session={activeSession}
                      diff={activeDiff}
                      onSelectCite={(f, l) => void handleOpenCite(f, l)}
                      onGoToViva={(starters) => {
                        if (starters.length > 0) setVivaStarters(starters);
                        selectTab("viva");
                      }}
                    />
                  </div>

                  <div
                    ref={(el) => {
                      panelRefs.current.viva = el;
                    }}
                    role="tabpanel"
                    id={`${baseId}-panel-viva`}
                    aria-labelledby={`${baseId}-tab-viva`}
                    className="tabpanel"
                  >
                    <VivaStudyPanel
                      session={activeSession}
                      starterQuestions={vivaStarters}
                      drillConcept={drillConcept}
                      onSelectCite={(f, l) => void handleOpenCite(f, l)}
                      onKnowledgeSaved={() => setKnowledgeVersion((v) => v + 1)}
                      onConsumeDrillConcept={() => setDrillConcept(null)}
                    />
                  </div>

                  <div
                    ref={(el) => {
                      panelRefs.current.knowledge = el;
                    }}
                    role="tabpanel"
                    id={`${baseId}-panel-knowledge`}
                    aria-labelledby={`${baseId}-tab-knowledge`}
                    className="tabpanel"
                  >
                    <KnowledgeHubPanel
                      activeSession={activeSession}
                      refreshTrigger={knowledgeVersion}
                      onDrillConcept={(c) => void handleDrillFromKnowledge(c)}
                      onSelectCite={(f, l, sid) => void handleOpenCite(f, l, sid)}
                    />
                  </div>
                </>
              )}
            </main>

            {footerNode}
            </div>
          </div>
        </div>
      )}

      <CiteDialog
        open={citeState.open}
        file={citeState.file}
        targetLine={citeState.line}
        lines={citeState.lines}
        loading={citeState.loading}
        error={citeState.error}
        onClose={() => setCiteState((prev) => ({ ...prev, open: false }))}
      />
    </div>
  );
}
export default App;
