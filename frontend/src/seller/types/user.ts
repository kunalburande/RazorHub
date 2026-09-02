export type Role = "Admin" | "Editor" | "Moderator" | "User" | "Seller" | "Customer";
export type Plan = "Free" | "Pro" | "Enterprise";
export type Status = "Active" | "Inactive" | "Suspended" | "Banned";

export type User = {
  id: string;
  avatar: string;
  fullName: string;
  email: string;
  role: Role;
  plan: Plan;
  status: Status;
  country: string;
  joinedAt: string;
  lastLogin: string;
};
