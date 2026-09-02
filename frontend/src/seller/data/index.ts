import { v4 as uuid } from "uuid";
import type { Category, FormInput, Product } from "../interfaces";

// ── Product catalog has been migrated to NeonDB PostgreSQL ──────────
// Products are loaded dynamically from the backend API via `/api/products/`.
export const productList: Product[] = [];

export const formInputsList: FormInput[] = [
  {
    id: "title",
    name: "title",
    label: "Product Title",
    type: "text",
  },
  {
    id: "description",
    name: "description",
    label: "Product Description",
    type: "text",
  },
  {
    id: "imageURL",
    name: "imageURL",
    label: "Product Image URL",
    type: "text",
  },
  {
    id: "price",
    name: "price",
    label: "Product Price (₹)",
    type: "text",
  },
];

export const colors: string[] = [
  "#121212",
  "#C0C0C0",
  "#13005A",
  "#3C2A21",
  "#820000",
  "#2563eb",
  "#10b981",
  "#f59e0b",
  "#f43f5e",
  "#06b6d4",
  "#8b5cf6",
  "#ea580c",
];

export const categories: Category[] = [
  {
    id: uuid(),
    name: "Electronics",
    imageURL:
      "https://i.pinimg.com/1200x/52/8f/cf/528fcf888642c11bd4b71e50b06b1446.jpg",
  },
  {
    id: uuid(),
    name: "Clothes",
    imageURL:
      "https://i.pinimg.com/736x/43/f9/3a/43f93a9825a88d5ce0e36e8c46d0f4cd.jpg",
  },
  {
    id: uuid(),
    name: "Photography",
    imageURL:
      "https://images.unsplash.com/photo-1544743744-48719693e9d9?w=700&auto=format&fit=crop&q=60&ixlib=rb-4.1.0",
  },
  {
    id: uuid(),
    name: "Furniture",
    imageURL:
      "https://images.unsplash.com/photo-1567016432779-094069958ea5?auto=format&fit=crop&w=200&q=80",
  },
  {
    id: uuid(),
    name: "Sneakers",
    imageURL:
      "https://images.unsplash.com/photo-1600185365926-3a2ce3cdb9eb?auto=format&fit=crop&w=200&q=80",
  },
  {
    id: uuid(),
    name: "Automotive",
    imageURL:
      "https://i.pinimg.com/736x/a3/c9/d0/a3c9d00d8dc9b8ac41d99b7dd429c43f.jpg",
  },
  {
    id: uuid(),
    name: "Accessories",
    imageURL:
      "https://i.pinimg.com/736x/59/39/e8/5939e895dc24015b03f3c1ba3c104f37.jpg",
  },
];
