"""本地 backend 启动脚本.

Notes:
    服务已有 runs 缓存和 SSE 通知，不负责启动 workflow。
"""

from __future__ import annotations

import uvicorn

HOST = "127.0.0.1"
PORT = 8010
RELOAD = True


def main() -> None:
    """启动 battle planner backend。"""

    uvicorn.run(
        "battle_planner.backend.app:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
    )


if __name__ == "__main__":
    main()
