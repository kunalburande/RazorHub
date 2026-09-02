import type { LocalizedText, Product } from "../interfaces";

export const getLocalizedText = (
  text: string | LocalizedText | undefined | null,
  _lang?: string,
): string => {
  if (!text) return "";
  if (typeof text === "string") return text;
  return text.en || Object.values(text)[0] || "";
};

export const getProductTitle = (product: Product, _lang?: string): string => {
  return getLocalizedText(product.title, _lang);
};

export const getProductDescription = (
  product: Product,
  _lang?: string,
): string => {
  return getLocalizedText(product.description, _lang);
};

export const formatCurrency = (value: number | string): string => {
  const num = typeof value === 'string' ? parseFloat(value.replace(/[^0-9.-]+/g, "")) : value;
  if (isNaN(num)) return typeof value === 'string' ? value : "₹0.00";
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(num);
};
