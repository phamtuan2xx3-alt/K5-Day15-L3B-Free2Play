"""Điểm vào bản chạy thử RepoKSV: CLI mặc định, --scan quét nhanh, và --serve khởi chạy FastAPI Web UI.

Chạy bằng:
  python run.py                         chạy CLI tương tác
  python codebase/app.py --serve        khởi chạy FastAPI + Web UI tại http://127.0.0.1:8000
  python codebase/app.py --scan S04     quét nhanh 1 hồ sơ hoặc link GitHub
"""
import argparse
import os
import sys

for _stream in (sys.stdout, sys.stderr, sys.stdin):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _where(e):
    """File (trong codebase/) gây lỗi khi nạp."""
    import traceback

    path = getattr(e, "filename", None) or (
        traceback.extract_tb(e.__traceback__)[-1].filename if e.__traceback__ else ""
    )
    if not path:
        return "codebase/"
    p = os.path.abspath(path)
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.relpath(p, base).replace(os.sep, "/") if p.startswith(base) else path


def _run_single_scan(target: str) -> int:
    import tracing
    from agent import answer

    tracing.begin("cli_scan")
    try:
        result = answer(target)
    except Exception as exc:
        tracing.end()
        print(f"[lỗi] {type(exc).__name__}: {exc}")
        return 1
    s, _ = tracing.end()
    print(result.get("output", "") if isinstance(result, dict) else result)
    print(
        "   (model: %s · gọi model %d lần · công cụ %d lần · token vào %d / ra %d)"
        % (", ".join(s["models"]) or "—", s["model_calls"], s["tool_calls"], s["tokens_in"], s["tokens_out"])
    )
    return 0


def _run_serve(host: str, port: int) -> int:
    try:
        import uvicorn
        import server
    except Exception as exc:
        print(f"Không nạp được FastAPI/uvicorn ({type(exc).__name__}: {exc}).")
        print("Cài thư viện web bằng: py -m pip install -r requirements.txt")
        return 1

    print(f"Đang khởi chạy RepoKSV Web UI tại http://{host}:{port}")
    uvicorn.run(server.app, host=host, port=port, log_level="info")
    return 0


def _run_cli() -> int:
    try:
        import tracing
        from agent import answer
    except Exception as e:
        print("Không nạp được codebase/ — lỗi ở %s: %s: %s" % (_where(e), type(e).__name__, e))
        print("Sửa lỗi rồi chạy lại. Cách nối model: docs/connect-model.md")
        return 1

    print("Bản chạy thử — gõ đầu vào rồi Enter. Thoát: Ctrl+C (hoặc Enter 2 lần với dòng trống).")
    blank = 0
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not text:
            blank += 1
            if blank >= 2:
                return 0
            continue
        blank = 0
        tracing.begin("app")
        try:
            result = answer(text)
        except NotImplementedError as e:
            tracing.end()
            print("Chưa nối model: %s" % e)
            return 1
        except Exception as e:
            tracing.end()
            print("[lỗi] %s: %s" % (type(e).__name__, e))
            continue
        s, _ = tracing.end()
        print(result.get("output", "") if isinstance(result, dict) else result)
        print(
            "   (model: %s · gọi model %d lần · công cụ %d lần · token vào %d / ra %d)"
            % (", ".join(s["models"]) or "—", s["model_calls"], s["tool_calls"], s["tokens_in"], s["tokens_out"])
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RepoKSV — Giám khảo ảo & Phản biện Bloom L0–L6")
    parser.add_argument("--serve", action="store_true", help="Khởi chạy FastAPI Web UI server")
    parser.add_argument("--host", default="127.0.0.1", help="Host lắng nghe khi --serve")
    parser.add_argument("--port", type=int, default=8000, help="Port lắng nghe khi --serve")
    parser.add_argument("--scan", default="", help="Quét nhanh 1 hồ sơ S01..S25 hoặc GitHub URL")
    args = parser.parse_args(argv)

    if args.serve:
        return _run_serve(args.host, args.port)
    if args.scan:
        return _run_single_scan(args.scan)
    return _run_cli()


if __name__ == "__main__":
    sys.exit(main())
