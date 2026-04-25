export type UserRole = "learner" | "admin";
export type UserStatus = "active" | "suspended";

export interface AuthUser {
  id: string;
  email: string;
  display_name?: string;
  role: UserRole;
  status?: UserStatus;
  created_at?: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  display_name: string;
}

export type RegisterResponse = AuthUser;

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}
