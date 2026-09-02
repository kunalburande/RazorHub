import axios from "axios";

import type { ChatMessage, DashboardContextData } from "../../types/ai";

interface SendMessageOptions {
  messages: ChatMessage[];
  context: DashboardContextData;
}

export async function sendChatMessage({
  messages,
  context,
}: SendMessageOptions): Promise<Partial<ChatMessage>> {
  const formattedMessages = messages.map((m) => ({
    role: m.role === "user" ? "user" : "assistant",
    content: m.content,
  }));

  const activeUsersCount = context.users.filter(
    (u) => u.status === "Active",
  ).length;

  try {
    const response = await axios.post<Partial<ChatMessage>>("/api/ai/chat/", {
      messages: formattedMessages,
      context: {
        platform: "dokkany",
        totalProducts: context.totalProducts,
        catalogValue: context.catalogValue,
        categoriesCount: context.uniqueCategoriesCount,
        avgPrice: context.averagePrice,
        totalUsers: context.users.length,
        activeUsers: activeUsersCount,
        lowStockCount: context.lowStockCount,
        outOfStockCount: context.outOfStockCount,
        products: context.products.map((p) => ({
          id: p.id,
          title: p.title,
          price: p.price,
          stock: p.stock ?? 15,
        })),
      },
    });

    return response.data;
  } catch (error: unknown) {
    if (axios.isAxiosError(error) && error.response?.data?.error) {
      throw new Error(error.response.data.error, { cause: error });
    }
    if (error instanceof Error) {
      throw error;
    }
    throw new Error("Failed to communicate with AI Assistant", { cause: error });
  }
}
