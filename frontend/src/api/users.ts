import type { User } from "../types/auth";
import { get, patch, post } from "./client";

export interface AdminUserCreate {
  first_name: string;
  last_name: string;
  dni: string;
  email: string;
  phone: string;
  password: string;
  role: User["role"];
}

export interface AdminUserUpdate {
  first_name?: string;
  last_name?: string;
  phone?: string;
  role?: User["role"];
  is_active?: boolean;
}

export function listUsers(): Promise<User[]> {
  return get<User[]>("/users");
}

export function createUser(data: AdminUserCreate): Promise<User> {
  return post<User>("/users", data);
}

export function updateUser(id: number, data: AdminUserUpdate): Promise<User> {
  return patch<User>(`/users/${id}`, data);
}