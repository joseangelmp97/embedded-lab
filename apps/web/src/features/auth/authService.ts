import { apiRequest } from "@/lib/apiClient";
import type {
  AuthUser,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse
} from "@/features/auth/types";

const AUTH_BASE_PATH = "/api/v1/auth";

export async function registerUser(payload: RegisterRequest): Promise<RegisterResponse> {
  return apiRequest<RegisterResponse>(`${AUTH_BASE_PATH}/register`, {
    method: "POST",
    body: payload
  });
}

export async function loginUser(payload: LoginRequest): Promise<LoginResponse> {
  return apiRequest<LoginResponse>(`${AUTH_BASE_PATH}/login`, {
    method: "POST",
    body: payload
  });
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  return apiRequest<AuthUser>("/api/v1/users/me", {
    auth: true
  });
}
