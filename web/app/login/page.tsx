"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/lib/stores/auth-store";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const login = useAuthStore((s) => s.login);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(username, password);
      router.push("/dashboard");
    } catch {
      setError("Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4">
        <h1 className="text-xl font-semibold">Sign in</h1>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full rounded-md border border-[var(--border-standard)] bg-[var(--surface-transparent-hover)] px-3 py-2 text-sm outline-none focus:border-[var(--brand)]"
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-md border border-[var(--border-standard)] bg-[var(--surface-transparent-hover)] px-3 py-2 text-sm outline-none focus:border-[var(--brand)]"
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-[var(--brand)] px-3 py-2 text-sm font-medium text-white hover:bg-[var(--brand)]/90 disabled:opacity-50"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>
        <p className="text-center text-sm text-[var(--text-secondary)]">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-[var(--brand)] hover:underline">
            Register
          </Link>
        </p>
      </form>
    </div>
  );
}
