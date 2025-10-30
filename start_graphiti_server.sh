#!/bin/bash

# 启动 Graphiti MCP 服务器的脚本
# 用于在启动 Claude Code 之前启动必要的依赖服务

echo "正在启动 Graphiti MCP 服务器..."

# 1. 启动 Neo4j Desktop
echo "启动 Neo4j Desktop..."
if [ -f "/home/czl/Downloads/localsend/neo4j-desktop-2.0.1-x86_64.AppImage" ]; then
    # 在后台启动 Neo4j Desktop
    nohup /home/czl/Downloads/localsend/neo4j-desktop-2.0.1-x86_64.AppImage > /tmp/neo4j-desktop.log 2>&1 &
    NEO4J_PID=$!
    echo "Neo4j Desktop 已启动，PID: $NEO4J_PID"
    
    # 等待 Neo4j Desktop 启动完成
    echo "等待 Neo4j Desktop 启动完成..."
    sleep 10
else
    echo "错误: 找不到 Neo4j Desktop AppImage 文件"
    exit 1
fi

# 2. 启动 Graphiti MCP 服务器
echo "启动 Graphiti MCP 服务器..."
if command -v uv &> /dev/null; then
    # 检查 graphiti_mcp_server.py 是否存在
    GRAPHITI_DIR="/home/czl/mcp/graphiti/mcp_server"
    if [ -f "$GRAPHITI_DIR/graphiti_mcp_server.py" ]; then
        cd "$GRAPHITI_DIR"
        uv run graphiti_mcp_server.py --transport sse &
        GRAPHITI_PID=$!
        echo "Graphiti MCP 服务器已启动，PID: $GRAPHITI_PID"
        echo "服务器运行在 SSE 传输模式"
        echo "执行目录: $GRAPHITI_DIR"
        
        # 保存进程 ID 以便后续管理
        echo $NEO4J_PID > /tmp/neo4j-desktop.pid
        echo $GRAPHITI_PID > /tmp/graphiti-mcp.pid
        
        echo "所有服务已启动完成！"
        echo "Neo4j Desktop PID: $NEO4J_PID"
        echo "Graphiti MCP 服务器 PID: $GRAPHITI_PID"
        echo ""
        echo "现在可以启动 Claude Code 了"
        echo ""
        echo "如需停止服务，请运行:"
        echo "kill $NEO4J_PID $GRAPHITI_PID"
        
    else
        echo "错误: 找不到 graphiti_mcp_server.py 文件"
        echo "请检查路径: $GRAPHITI_DIR/graphiti_mcp_server.py"
        # 清理已启动的 Neo4j Desktop
        kill $NEO4J_PID 2>/dev/null
        exit 1
    fi
else
    echo "错误: 找不到 uv 命令，请确保已安装 uv"
    # 清理已启动的 Neo4j Desktop
    kill $NEO4J_PID 2>/dev/null
    exit 1
fi