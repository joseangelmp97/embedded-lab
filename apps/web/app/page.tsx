"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/features/auth/useAuth";

export default function HomePage() {
  const {
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
  } = useAuth();

  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [registerDisplayName, setRegisterDisplayName] = useState("");

  const onLoginSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await handleLogin({ email: loginEmail, password: loginPassword });
  };

  const onRegisterSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await handleRegister({
      email: registerEmail,
      password: registerPassword,
      displayName: registerDisplayName
    });
  };

  const displayName = user?.display_name?.trim() || "Learner";

  if (user) {
    return (
      <div className="private-shell">
        <header className="shell-header">
          <div className="shell-brand">
            <p className="shell-eyebrow">Embedded Lab</p>
            <h1 className="shell-title">Learning Dashboard</h1>
          </div>

          <div className="shell-user">
            <p className="shell-user-name">{displayName}</p>
            <p className="shell-user-email">{user.email}</p>
            <button type="button" className="button secondary shell-logout" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </header>

        <main className="shell-main">
          <section className="welcome-card" aria-label="User account summary">
            <h2>Welcome back, {displayName}</h2>
            <p className="subtitle">Continue your embedded systems learning path and keep your streak alive.</p>

            {error ? <p className="feedback error">{error}</p> : null}
            {successMessage ? <p className="feedback success">{successMessage}</p> : null}

            <dl className="user-meta-grid">
              <div>
                <dt>Role</dt>
                <dd>{user.role}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>{user.status ?? "unknown"}</dd>
              </div>
              <div>
                <dt>Email</dt>
                <dd>{user.email}</dd>
              </div>
            </dl>
          </section>

          <section className="feature-grid" aria-label="Dashboard sections">
            <article className="feature-card">
              <h3>Labs</h3>
              <p>Browse practical lab challenges with estimated time and difficulty before starting.</p>
              <Link href="/labs" className="button secondary feature-card-action">
                Open Labs
              </Link>
            </article>
            <article className="feature-card">
              <h3>Learning Content</h3>
              <p>Browse tracks, levels, and challenge sets tailored to your current progress.</p>
            </article>
            <article className="feature-card">
              <h3>Lab Attempts</h3>
              <p>Resume unfinished attempts and review feedback from previous submissions.</p>
            </article>
            <article className="feature-card">
              <h3>Profile & Progress</h3>
              <p>Track completed milestones and monitor your next progression target.</p>
            </article>
            <article className="feature-card">
              <h3>Leaderboard</h3>
              <p>Compare your points with peers and discover where to improve your score.</p>
            </article>
          </section>
        </main>
      </div>
    );
  }

  return (
    <main className="public-auth-page">
      <section className="public-intro" aria-label="Platform introduction">
        <p className="shell-eyebrow">Embedded Lab</p>
        <h1 className="title">Build practical embedded systems skills</h1>
        <p className="subtitle">
          Sign in to continue your progress or create an account to start solving microcontroller and electronics
          challenges.
        </p>
      </section>

      <section className="card auth-card" aria-label="Authentication">
        <h2 className="auth-heading">{view === "login" ? "Welcome back" : "Create your account"}</h2>

        {isInitializing ? <p className="feedback">Loading current session...</p> : null}
        {error ? <p className="feedback error">{error}</p> : null}
        {successMessage ? <p className="feedback success">{successMessage}</p> : null}

        <div className="tabs" role="tablist" aria-label="Authentication options">
          <button
            type="button"
            role="tab"
            aria-selected={view === "login"}
            className={`tab ${view === "login" ? "active" : ""}`}
            onClick={() => setView("login")}
            disabled={isSubmitting}
          >
            Login
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={view === "register"}
            className={`tab ${view === "register" ? "active" : ""}`}
            onClick={() => setView("register")}
            disabled={isSubmitting}
          >
            Register
          </button>
        </div>

        {view === "login" ? (
          <form className="row" onSubmit={onLoginSubmit} noValidate>
            <label className="field-label" htmlFor="login-email">
              Email
            </label>
            <input
              id="login-email"
              className="input"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              value={loginEmail}
              onChange={(event) => setLoginEmail(event.target.value)}
              required
            />

            <label className="field-label" htmlFor="login-password">
              Password
            </label>
            <input
              id="login-password"
              className="input"
              type="password"
              autoComplete="current-password"
              placeholder="Enter your password"
              value={loginPassword}
              onChange={(event) => setLoginPassword(event.target.value)}
              required
            />

            <button className="button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Signing in..." : "Login"}
            </button>
          </form>
        ) : (
          <form className="row" onSubmit={onRegisterSubmit} noValidate>
            <label className="field-label" htmlFor="register-display-name">
              Display name
            </label>
            <input
              id="register-display-name"
              className="input"
              type="text"
              autoComplete="name"
              placeholder="Your name"
              value={registerDisplayName}
              onChange={(event) => setRegisterDisplayName(event.target.value)}
              required
            />

            <label className="field-label" htmlFor="register-email">
              Email
            </label>
            <input
              id="register-email"
              className="input"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              value={registerEmail}
              onChange={(event) => setRegisterEmail(event.target.value)}
              required
            />

            <label className="field-label" htmlFor="register-password">
              Password
            </label>
            <input
              id="register-password"
              className="input"
              type="password"
              autoComplete="new-password"
              placeholder="Create a secure password"
              value={registerPassword}
              onChange={(event) => setRegisterPassword(event.target.value)}
              required
            />

            <button className="button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating account..." : "Register"}
            </button>
          </form>
        )}
      </section>
    </main>
  );
}
