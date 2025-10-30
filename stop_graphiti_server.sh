#!/bin/bash

# 停止 Graphiti MCP 服务器的脚本

echo "正在停止 Graphiti MCP 服务器..."

# 从 PID 文件读取进程 ID 并停止
if [ -f "/tmp/neo4j-desktop.pid" ]; then
    NEO4J_PID=$(cat /tmp/neo4j-desktop.pid)
    echo "停止 Neo4j Desktop (PID: $NEO4J_PID)..."
    kill $NEO4J_PID 2>/dev/null
    rm /tmp/neo4j-desktop.pid
    echo "Neo4j Desktop 已停止"
fi

if [ -f "/tmp/graphiti-mcp.pid" ]; then
    GRAPHITI_PID=$(cat /tmp/graphiti-mcp.pid)
    echo "停止 Graphiti MCP 服务器 (PID: $GRAPHITI_PID)..."
    kill $GRAPHITI_PID 2>/dev/null
    rm /tmp/graphiti-mcp.pid
    echo "Graphiti MCP 服务器已停止"
fi

# 额外检查相关进程
echo "检查相关进程..."
pkill -f "neo4j-desktop" 2>/dev/null
pkill -f "graphiti_mcp_server" 2>/dev/null

echo "所有服务已停止"