import { useCallback, useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
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
import { ExportPanel } from "@/components/ExportPanel.tsx";
import { LegalPage } from "@/components/LegalPages.tsx";
import { ScanSidebar } from "@/components/ScanSidebar.tsx";
import { TopBar } from "@/components/TopBar.tsx";
import { VivaStudyPanel } from "@/components/VivaStudyPanel.tsx";
import { Alert } from "@/components/ui/alert.tsx";
import { Button } from "@/components/ui/button.tsx";
import type {
  FileLineItem,
  MeResponse,
  ScanDiffSummary,
  ScanSessionDetail,
  ScanSessionSummary,
  ScanStreamState,
  SubmissionOption,
} from "@/types.ts";
import { extractUrlHackTarget } from "@/utils/citations.ts";

type TabId = "audit" | "viva" | "export";

const TABS: Array<{ id: TabId; label: string }> = [
  { id: "audit", label: "Soi Repo" },
  { id: "viva", label: "Vấn đáp Bloom" },
  { id: "export", label: "Xuất file" },
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
  const baseId = useId();
  const tabRefs = useRef<Record<TabId, HTMLButtonElement | null>>({
    audit: null,
    viva: null,
    export: null,
  });
  const panelRefs = useRef<Record<TabId, HTMLDivElement | null>>({
    audit: null,
    viva: null,
    export: null,
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

  // Sync hidden="until-found" and beforematch
  useEffect(() => {
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
    tabRefs.current[tabId]?.scrollIntoView({ block: "nearest", inline: "nearest" });
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
      tabRefs.current[nextTab]?.focus();
    }
  };

  const handleOpenCite = useCallback(
    async (file: string, line: number) => {
      if (!activeSession) return;
      setCiteState({
        open: true,
        file,
        line,
        lines: [],
        loading: true,
        error: null,
      });
      try {
        const res = await getFileLines(activeSession.scan_id, file, line);
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

  const isLegalRoute = pathname === "/login" || pathname === "/privacy" || pathname === "/terms";

  const footerNode = (
    <footer className="border-t border-border bg-card/60 px-4 py-3 text-xs text-muted-foreground sm:px-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
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
    <div className="flex min-h-screen flex-col bg-background text-foreground">
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
        <div className="grid flex-1 grid-cols-1 lg:grid-cols-[260px_minmax(0,1fr)]">
          <ScanSidebar
            sessions={sessions}
            activeScanId={activeSession?.scan_id ?? null}
            onSelectSession={(id) => void handleSelectSession(id)}
            loading={sessionsLoading}
            me={me}
            onNavigate={navigate}
          />

          <div className="order-first lg:order-last flex min-w-0 flex-col bg-background">
            <TopBar
              targetInput={targetInput}
              onTargetInputChange={setTargetInput}
              submissions={submissions}
              scanning={scanning}
              onScan={(t, force) => void handleScan(t, force)}
              onNavigate={navigate}
            />

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
                <div className="tabpanel-inner space-y-3">
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
                <div className="tabpanel-inner space-y-3">
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
                  <div
                    role="tablist"
                    aria-label="Khu vực làm việc RepoKSV"
                    className="flex overflow-x-auto border-b border-border bg-card/40 px-4 sm:px-6 gap-1"
                    onKeyDown={handleTabKeyDown}
                  >
                    {TABS.map((tab) => {
                      const selected = activeTab === tab.id;
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
                          {tab.label}
                        </button>
                      );
                    })}
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
                      onSelectCite={(f, l) => void handleOpenCite(f, l)}
                    />
                  </div>

                  <div
                    ref={(el) => {
                      panelRefs.current.export = el;
                    }}
                    role="tabpanel"
                    id={`${baseId}-panel-export`}
                    aria-labelledby={`${baseId}-tab-export`}
                    className="tabpanel"
                  >
                    <ExportPanel session={activeSession} />
                  </div>
                </>
              )}
            </main>

            {footerNode}
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
