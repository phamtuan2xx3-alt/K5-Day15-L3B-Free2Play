interface LegalPageProps {
  route: "/login" | "/privacy" | "/terms";
  onNavigate: (path: string) => void;
}

const APP_ORIGIN = "https://repoksv.tuanpq.com";
const CONTACT_EMAIL = "contact@tuanpq.com";

export function LegalPage({ route, onNavigate }: LegalPageProps) {
  const backLink = (
    <div style={{ marginBottom: "1rem" }}>
      <a
        href="/"
        className="btn btn-secondary"
        onClick={(e) => {
          e.preventDefault();
          onNavigate("/");
        }}
      >
        Về trang chính
      </a>
    </div>
  );

  if (route === "/login") {
    return (
      <main id="main-content" className="static-page" tabIndex={-1}>
        {backLink}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem" }}>
          <img src="/repoksv-logo-120.png" alt="Logo RepoKSV" className="brand-logo" width={42} height={42} />
          <h1 style={{ margin: 0 }}>Đăng nhập RepoKSV</h1>
        </div>
        <p>
          Đăng nhập qua Google OAuth 2.0 (PKCE) để lưu lịch sử phiên quét và hồ sơ thông hiểu Bloom L0–L6 riêng của bạn.
          RepoKSV chỉ yêu cầu 3 quyền cơ bản: <code>openid</code>, <code>email</code>, <code>profile</code>.
        </p>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", marginBlock: "1.25rem" }}>
          <a className="btn btn-primary btn-google" href="/auth/google">
            <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24">
              <path fill="currentColor" d="M21.8 12.23c0-.68-.06-1.36-.18-2.02H12v3.83h5.5a4.7 4.7 0 0 1-2.04 3.09v2.56h3.3c1.93-1.78 3.04-4.4 3.04-7.46ZM12 22c2.75 0 5.06-.91 6.75-2.47l-3.3-2.56c-.91.61-2.08.97-3.45.97-2.65 0-4.9-1.79-5.7-4.2H2.89v2.64A10 10 0 0 0 12 22ZM6.3 13.74A5.98 5.98 0 0 1 6 12c0-.6.1-1.19.3-1.74V7.62H2.89A10 10 0 0 0 2 12c0 1.61.39 3.14 1.09 4.38l3.21-2.64ZM12 6.06c1.5 0 2.84.52 3.9 1.53l2.92-2.92C17.05 2.99 14.74 2 12 2a10 10 0 0 0-9.11 5.62l3.41 2.64C7.1 7.85 9.35 6.06 12 6.06Z" />
            </svg>
            Google Sign-In
          </a>
          <a
            className="btn btn-secondary"
            href="/privacy"
            onClick={(e) => {
              e.preventDefault();
              onNavigate("/privacy");
            }}
          >
            Quyền riêng tư
          </a>
        </div>
        <hr />
        <h2 style={{ fontSize: "1.05rem" }}>Cấu hình Google OAuth (Admin)</h2>
        <pre className="code-preview">
          {`Authorized JavaScript origin: ${APP_ORIGIN}\nAuthorized redirect URI:    ${APP_ORIGIN}/auth/google/callback`}
        </pre>
      </main>
    );
  }

  if (route === "/privacy") {
    return (
      <main id="main-content" className="static-page" tabIndex={-1}>
        {backLink}
        <article>
          <h1 style={{ marginTop: 0 }}>Chính sách quyền riêng tư (Privacy Policy) — RepoKSV</h1>
          <p>
            <strong>Ngày hiệu lực:</strong> 28/11/2026 · <strong>Tên ứng dụng:</strong> RepoKSV (Repo Kiểm Sát Viên) ·{" "}
            <strong>Tên miền:</strong> <a href={APP_ORIGIN}>{APP_ORIGIN}</a>
          </p>
          <h2>1. Dữ liệu nhận qua Google OAuth 2.0</h2>
          <p>
            RepoKSV chỉ xin các quyền cơ bản <code>openid</code>, <code>email</code>, <code>profile</code> để định danh phiên làm việc cá nhân,
            hiển thị tên/email/ảnh đại diện và tách riêng lịch sử Bloom Memory. Ứng dụng không đọc Gmail, Drive hay bất kỳ dữ liệu nhạy cảm nào khác.
          </p>
          <h2>2. Quyền riêng tư mã nguồn &amp; lưu trữ</h2>
          <ul>
            <li>Repo GitHub công khai chỉ được đọc tạm trong RAM khi quét; không lưu nguyên mã nguồn bài nộp của đội khác xuống đĩa hoặc database.</li>
            <li>Cookie phiên được ký HMAC-SHA256 (<code>HttpOnly</code>, <code>Secure</code>, <code>SameSite=Lax</code>) và tự hết hạn sau 7 ngày hoặc khi Đăng xuất.</li>
            <li>Không bán, chia sẻ hay dùng dữ liệu cho quảng cáo; tuân thủ Google API Services User Data Policy (Limited Use).</li>
          </ul>
          <h2>3. Liên hệ &amp; xoá dữ liệu</h2>
          <p>
            Mọi yêu cầu truy xuất hoặc xoá dữ liệu xin liên hệ <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>.
          </p>
        </article>
      </main>
    );
  }

  return (
    <main id="main-content" className="static-page" tabIndex={-1}>
      {backLink}
      <article>
        <h1 style={{ marginTop: 0 }}>Điều khoản sử dụng (Terms of Service) — RepoKSV</h1>
        <p>
          <strong>Cập nhật:</strong> 28/11/2026 · <strong>Ứng dụng:</strong> RepoKSV (<a href={APP_ORIGIN}>{APP_ORIGIN}</a>)
        </p>
        <h2>1. Giới hạn trách nhiệm (NO-AUTO-GRADE)</h2>
        <ul>
          <li>RepoKSV hỗ trợ rà soát lỗi cứng, kiểm chứng trích dẫn <code>file:Lxx</code> và luyện phản biện theo thang Bloom L0–L6.</li>
          <li>Kết quả không thay thế điểm số chính thức từ giảng viên, Lab Coach hay hội đồng chấm bài.</li>
        </ul>
        <h2>2. Trách nhiệm người dùng</h2>
        <ul>
          <li>Không đưa API key thật, mật khẩu hoặc thông tin cá nhân nhạy cảm (PII) vào ô nhập liệu công khai.</li>
          <li>Không lạm dụng công cụ để dò quét trái phép hoặc vượt hạn mức tài nguyên hệ thống.</li>
        </ul>
        <p>
          Liên hệ hỗ trợ: <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>.
        </p>
      </article>
    </main>
  );
}
