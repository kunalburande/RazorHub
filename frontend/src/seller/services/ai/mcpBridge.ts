/**
 * Model Context Protocol (MCP) Bridge for RazorHub & Dokkany Agent Suite
 * Provides standardized MCP Tool Schemas and JSON-RPC tool invocation handlers
 * for integrating multi-agent frameworks (Claude MCP, OpenAI Agents, Gemini, Antigravity).
 */

import { AI_TOOLS } from"./aiTools";
import { executeTool } from"./toolExecutor";
import type { Product } from"../../interfaces";
import type { User } from"../../types/user";
import type { ToolName } from"../../types/ai";

export interface McpToolSchema {
 name: string;
 description: string;
 inputSchema: {
 type:"object";
 properties: Record<string, unknown>;
 required?: string[];
 };
}

/**
 * Returns all Dokkany tools formatted according to the official MCP Protocol Schema specification
 */
export function getMcpToolsList(): McpToolSchema[] {
 return AI_TOOLS.map((tool) => ({
 name: tool.name,
 description: tool.description,
 inputSchema: {
 type:"object",
 properties: tool.parameters.properties,
 required: tool.parameters.required,
 },
 }));
}

/**
 * Dispatches an MCP JSON-RPC `tools/call` request
 */
export function handleMcpToolCall({
 name,
 arguments: args,
 products,
 users,
}: {
 name: string;
 arguments: Record<string, unknown>;
 products: Product[];
 users: User[];
}) {
 const isKnownTool = AI_TOOLS.some((t) => t.name === name);
 if (!isKnownTool) {
 return {
 isError: true,
 content: [{ type:"text", text: `Unknown MCP tool:"${name}"` }],
 };
 }

 try {
 const result = executeTool({
 toolName: name as ToolName,
 args,
 products,
 users,
 });

 return {
 isError: false,
 content: [
 {
 type:"text",
 text: typeof result.result ==="string" ? result.result : JSON.stringify(result.result, null, 2),
 },
 ],
 structuredData: result.result,
 };
 } catch (err) {
 const errorMsg = err instanceof Error ? err.message : String(err);
 return {
 isError: true,
 content: [{ type:"text", text: `Error executing tool"${name}": ${errorMsg}` }],
 };
 }
}
