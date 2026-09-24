import { get, post } from "./client";
import type { User } from "../types/auth";

export interface RegisterData {
  first_name: string;
  last_name: string;
  dni: string;
  email: string;
  phone: string;
  password: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export function register(data: RegisterData): Promise<User> {
  return post<User>("/auth/register", data);
}

export function login(data: LoginData): Promise<TokenResponse> {
  return post<TokenResponse>("/auth/login", data);
}

export function fetchMe(): Promise<User> {
  return get<User>("/auth/me");
}

export function logout(): Promise<{ message: string }> {
  return post("/auth/logout", {});
}