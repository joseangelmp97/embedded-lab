"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiClientError } from "@/lib/apiClient";
import { clearAccessToken, readAccessToken, saveAccessToken } from "@/lib/storage";
import { fetchCurrentUser, loginUser, registerUser } from "@/features/auth/authService";
import type { AuthUser } from "@/features/auth/types";

type AuthView = "login" | "register";

interface RegisterInput {
  email: string;
  password: string;
  displayName: string;
}

interface LoginInput {
  email: string;
  password: string;
}

export function useAuth() {
  const [view, setView] = useState<AuthView>("login");
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadCurrentUser = useCallback(async () => {
    const token = readAccessToken();

    if (!token) {
      setIsInitializing(false);
      return;
    }

    try {
      const me = await fetchCurrentUser();
      setUser(me);
    } catch (caughtError) {
      clearAccessToken();
      setUser(null);

      if (caughtError instanceof ApiClientError && caughtError.status !== 401) {
        setError(caughtError.message);
      }
    } finally {
      setIsInitializing(false);
    }
  }, []);

  useEffect(() => {
    void loadCurrentUser();
  }, [loadCurrentUser]);

  const handleRegister = useCallback(async (input: RegisterInput) => {
    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await registerUser({
        email: input.email,
        password: input.password,
        display_name: input.displayName
      });

      setSuccessMessage("Registration complete. Please login with your credentials.");
      setView("login");
    } catch (caughtError) {
      if (caughtError instanceof Error) {
        setError(caughtError.message);
      } else {
        setError("Registration failed.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  const handleLogin = useCallback(async (input: LoginInput) => {
    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const loginResponse = await loginUser(input);
      saveAccessToken(loginResponse.access_token);
      const me = await fetchCurrentUser();
      setUser(me);
      setSuccessMessage("You are now logged in.");
    } catch (caughtError) {
      clearAccessToken();
      setUser(null);

      if (caughtError instanceof Error) {
        setError(caughtError.message);
      } else {
        setError("Login failed.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  const handleLogout = useCallback(() => {
    clearAccessToken();
    setUser(null);
    setError(null);
    setSuccessMessage("Logged out successfully.");
    setView("login");
  }, []);

  return {
    view,
    setView,
    user,
    isInitializing,
    isSubmitting,
    error,
    successMessage,
    handleRegister,
    handleLogin,
    handleLogout
  };
}
