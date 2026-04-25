#!/bin/bash
# Report Editor 开发脚本
# 用法: bash scripts/editor.sh <command>

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_PORT=8070
FRONTEND_PORT=3070

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

usage() {
    echo -e "${CYAN}Report Editor 开发脚本${NC}"
    echo ""
    echo "用法: bash scripts/editor.sh <command>"
    echo ""
    echo "命令:"
    echo -e "  ${GREEN}dev${NC}            启动前后端开发服务器"
    echo -e "  ${GREEN}backend${NC}        仅启动后端 (port $BACKEND_PORT)"
    echo -e "  ${GREEN}frontend${NC}       仅启动前端 (port $FRONTEND_PORT)"
    echo -e "  ${GREEN}install${NC}        安装所有依赖"
    echo -e "  ${GREEN}test${NC}           运行后端测试 (pytest)"
    echo -e "  ${GREEN}test-api${NC}       运行 API 集成测试"
    echo -e "  ${GREEN}lint${NC}           运行前端类型检查"
    echo -e "  ${GREEN}build${NC}          构建前端生产版本"
    echo -e "  ${GREEN}clean${NC}          清理临时文件和数据库"
    echo -e "  ${GREEN}reset-db${NC}       重置数据库"
    echo -e "  ${GREEN}stop${NC}           停止所有开发服务"
    echo -e "  ${GREEN}status${NC}         检查服务状态"
}

# ── 安装依赖 ──────────────────────────────────────────────
install() {
    echo -e "${CYAN}安装后端依赖...${NC}"
    cd "$PROJECT_DIR"
    pip install -r server/requirements.txt
    pip install -e ".[dev]"

    echo -e "${CYAN}安装前端依赖...${NC}"
    cd "$PROJECT_DIR/web"
    npm install

    echo -e "${GREEN}所有依赖安装完成${NC}"
}

# ── 启动后端 ──────────────────────────────────────────────
backend() {
    echo -e "${CYAN}启动后端服务 (port $BACKEND_PORT)...${NC}"
    cd "$PROJECT_DIR"
    uvicorn server.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload
}

# ── 启动前端 ──────────────────────────────────────────────
frontend() {
    echo -e "${CYAN}启动前端服务 (port $FRONTEND_PORT)...${NC}"
    cd "$PROJECT_DIR/web"
    npm run dev
}

# ── 同时启动前后端 ────────────────────────────────────────
dev() {
    echo -e "${CYAN}启动 Report Editor 开发环境...${NC}"
    echo -e "  后端: ${GREEN}http://localhost:$BACKEND_PORT${NC}"
    echo -e "  前端: ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
    echo ""

    # 后端放后台
    cd "$PROJECT_DIR"
    uvicorn server.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload &
    BACKEND_PID=$!
    echo -e "${GREEN}后端 PID: $BACKEND_PID${NC}"

    # 等后端启动
    sleep 2

    # 前端放后台
    cd "$PROJECT_DIR/web"
    npm run dev &
    FRONTEND_PID=$!
    echo -e "${GREEN}前端 PID: $FRONTEND_PID${NC}"

    echo ""
    echo -e "${GREEN}开发环境已启动！按 Ctrl+C 停止所有服务${NC}"

    # 捕获退出信号
    trap "echo -e '${YELLOW}停止服务...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

    wait
}

# ── 运行后端测试 ──────────────────────────────────────────
test() {
    echo -e "${CYAN}运行后端测试...${NC}"
    cd "$PROJECT_DIR"
    pytest tests/ -v
}

# ── API 集成测试 ──────────────────────────────────────────
test_api() {
    echo -e "${CYAN}API 集成测试...${NC}"

    BASE="http://localhost:$BACKEND_PORT"

    # Health check
    echo -e "${YELLOW}1. Health check...${NC}"
    curl -s "$BASE/api/health" | python3 -m json.tool

    # Register
    echo -e "${YELLOW}2. Register test user...${NC}"
    curl -s -X POST "$BASE/api/auth/register" \
        -H "Content-Type: application/json" \
        -d '{"username":"testuser","password":"test123"}' | python3 -m json.tool || true

    # Login
    echo -e "${YELLOW}3. Login...${NC}"
    TOKEN=$(curl -s -X POST "$BASE/api/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"testuser","password":"test123"}' \
        | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
    echo -e "  Token: ${GREEN}${TOKEN:0:20}...${NC}"

    # Upload template
    echo -e "${YELLOW}4. Upload template...${NC}"
    TEMPLATE_RESP=$(curl -s -X POST "$BASE/api/templates" \
        -H "Authorization: Bearer $TOKEN" \
        -F "file=@$PROJECT_DIR/templates/test_all_blocks.docx")
    TEMPLATE_ID=$(echo "$TEMPLATE_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
    echo -e "  Template ID: ${GREEN}$TEMPLATE_ID${NC}"

    # List templates
    echo -e "${YELLOW}5. List templates...${NC}"
    curl -s "$BASE/api/templates" \
        -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; data=json.load(sys.stdin); print(f'  Found {len(data)} template(s)')"

    # Create draft
    echo -e "${YELLOW}6. Create draft...${NC}"
    DRAFT_RESP=$(curl -s -X POST "$BASE/api/drafts" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"template_id\":\"$TEMPLATE_ID\",\"title\":\"Test Report\"}")
    DRAFT_ID=$(echo "$DRAFT_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
    echo -e "  Draft ID: ${GREEN}$DRAFT_ID${NC}"

    # Update draft
    echo -e "${YELLOW}7. Update draft...${NC}"
    curl -s -X PATCH "$BASE/api/drafts/$DRAFT_ID" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"title":"Updated Test Report"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Title: {d[\"title\"]}')"

    # Export
    echo -e "${YELLOW}8. Export .docx...${NC}"
    curl -s -X POST "$BASE/api/drafts/$DRAFT_ID/export" \
        -H "Authorization: Bearer $TOKEN" \
        -o "$PROJECT_DIR/output/test_export.docx"
    echo -e "  输出: ${GREEN}$PROJECT_DIR/output/test_export.docx${NC}"

    echo ""
    echo -e "${GREEN}API 集成测试完成！${NC}"
}

# ── 前端类型检查 ──────────────────────────────────────────
lint() {
    echo -e "${CYAN}运行前端类型检查...${NC}"
    cd "$PROJECT_DIR/web"
    npx tsc --noEmit
}

# ── 构建前端 ──────────────────────────────────────────────
build() {
    echo -e "${CYAN}构建前端生产版本...${NC}"
    cd "$PROJECT_DIR/web"
    npm run build
}

# ── 清理 ──────────────────────────────────────────────────
clean() {
    echo -e "${YELLOW}清理临时文件...${NC}"
    cd "$PROJECT_DIR"

    # 清理 Python 缓存
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

    # 清理 Next.js 缓存
    rm -rf web/.next

    # 清理输出
    rm -rf output/*.docx

    echo -e "${GREEN}清理完成${NC}"
}

# ── 重置数据库 ────────────────────────────────────────────
reset_db() {
    echo -e "${YELLOW}重置数据库...${NC}"
    cd "$PROJECT_DIR"
    rm -f data/editor.db
    echo -e "${GREEN}数据库已重置${NC}"
}

# ── 停止服务 ──────────────────────────────────────────────
stop() {
    echo -e "${YELLOW}停止开发服务...${NC}"
    pkill -f "uvicorn server.main:app" 2>/dev/null && echo -e "  ${GREEN}后端已停止${NC}" || echo -e "  ${YELLOW}后端未在运行${NC}"
    pkill -f "next dev" 2>/dev/null && echo -e "  ${GREEN}前端已停止${NC}" || echo -e "  ${YELLOW}前端未在运行${NC}"
}

# ── 检查状态 ──────────────────────────────────────────────
status() {
    echo -e "${CYAN}服务状态:${NC}"

    # 后端
    if curl -s "http://localhost:$BACKEND_PORT/api/health" > /dev/null 2>&1; then
        echo -e "  后端 (port $BACKEND_PORT): ${GREEN}运行中${NC}"
    else
        echo -e "  后端 (port $BACKEND_PORT): ${RED}未运行${NC}"
    fi

    # 前端
    if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
        echo -e "  前端 (port $FRONTEND_PORT): ${GREEN}运行中${NC}"
    else
        echo -e "  前端 (port $FRONTEND_PORT): ${RED}未运行${NC}"
    fi
}

# ── 主入口 ────────────────────────────────────────────────
case "${1:-}" in
    dev)        dev ;;
    backend)    backend ;;
    frontend)   frontend ;;
    install)    install ;;
    test)       test ;;
    test-api)   test_api ;;
    lint)       lint ;;
    build)      build ;;
    clean)      clean ;;
    reset-db)   reset_db ;;
    stop)       stop ;;
    status)     status ;;
    *)          usage ;;
esac
