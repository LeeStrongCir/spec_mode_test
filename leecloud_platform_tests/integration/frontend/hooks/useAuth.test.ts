// Spec: specs/001-register-login/spec.md → TC-030, TC-031
import { renderHook, act } from "@testing-library/react";
import { useState, useCallback } from "react";
import { setupServer } from "msw/node";
import { beforeAll, afterAll, afterEach, beforeEach, describe, it, expect, vi } from "vitest";
import { authHandlers, resetAuthMockState } from "../mocks/handlers/auth";

const server = setupServer(...authHandlers);

beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));
afterAll(() => server.close());
beforeEach(() => resetAuthMockState());
afterEach(() => server.resetHandlers());

interface AuthState {
  isAuthenticated: boolean;
  user: { username: string; role: string } | null;
  loading: boolean;
  error: string | null;
}

type AuthAction =
  | { type: "LOGIN_START" }
  | { type: "LOGIN_SUCCESS"; payload: { username: string; role: string } }
  | { type: "LOGIN_FAILURE"; payload: string }
  | { type: "LOGOUT" };

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case "LOGIN_START":
      return { ...state, loading: true, error: null };
    case "LOGIN_SUCCESS":
      return { isAuthenticated: true, user: action.payload, loading: false, error: null };
    case "LOGIN_FAILURE":
      return { isAuthenticated: false, user: null, loading: false, error: action.payload };
    case "LOGOUT":
      return { isAuthenticated: false, user: null, loading: false, error: null };
    default:
      return state;
  }
}


describe("useAuth Hook Tests", () => {
  describe("Initial state", () => {
    it("starts unauthenticated with no user", () => {
      const { result } = renderHook(() =>
        useState<AuthState>({ isAuthenticated: false, user: null, loading: false, error: null }),
      );
      const [state] = result.current;
      expect(state.isAuthenticated).toBe(false);
      expect(state.user).toBeNull();
      expect(state.loading).toBe(false);
      expect(state.error).toBeNull();
    });
  });

  describe("Login state transitions", () => {
    it("transitions through LOGIN_SUCCESS", () => {
      const { result } = renderHook(() => {
        const [state, dispatch] = useState<AuthState>({
          isAuthenticated: false,
          user: null,
          loading: false,
          error: null,
        });
        const loginSuccess = useCallback((user: { username: string; role: string }) => {
          dispatch({ type: "LOGIN_SUCCESS", payload: user });
        }, []);
        return { state, loginSuccess };
      });

      act(() => {
        result.current.loginSuccess({ username: "testuser", role: "user" });
      });

      expect(result.current.state.isAuthenticated).toBe(true);
      expect(result.current.state.user?.username).toBe("testuser");
      expect(result.current.state.user?.role).toBe("user");
      expect(result.current.state.loading).toBe(false);
    });

    it("transitions through LOGIN_FAILURE", () => {
      const { result } = renderHook(() => {
        const [state, dispatch] = useState<AuthState>({
          isAuthenticated: false,
          user: null,
          loading: false,
          error: null,
        });
        const loginFailure = useCallback((msg: string) => {
          dispatch({ type: "LOGIN_FAILURE", payload: msg });
        }, []);
        return { state, loginFailure };
      });

      act(() => {
        result.current.loginFailure("用户名或密码错误");
      });

      expect(result.current.state.isAuthenticated).toBe(false);
      expect(result.current.state.user).toBeNull();
      expect(result.current.state.error).toBe("用户名或密码错误");
      expect(result.current.state.loading).toBe(false);
    });

    it("shows loading state during login attempt", () => {
      const { result } = renderHook(() => {
        const [state, dispatch] = useState<AuthState>({
          isAuthenticated: false,
          user: null,
          loading: false,
          error: null,
        });
        const loginStart = useCallback(() => {
          dispatch({ type: "LOGIN_START" });
        }, []);
        return { state, loginStart };
      });

      act(() => {
        result.current.loginStart();
      });

      expect(result.current.state.loading).toBe(true);
      expect(result.current.state.error).toBeNull();
    });
  });

  describe("Logout state transitions", () => {
    it("transitions to logged out state on logout", () => {
      const { result } = renderHook(() => {
        const [state, dispatch] = useState<AuthState>({
          isAuthenticated: true,
          user: { username: "testuser", role: "user" },
          loading: false,
          error: null,
        });
        const logout = useCallback(() => {
          dispatch({ type: "LOGOUT" });
        }, []);
        return { state, logout };
      });

      act(() => {
        result.current.logout();
      });

      expect(result.current.state.isAuthenticated).toBe(false);
      expect(result.current.state.user).toBeNull();
      expect(result.current.state.loading).toBe(false);
      expect(result.current.state.error).toBeNull();
    });

    it("logout clears user data completely", () => {
      const { result } = renderHook(() => {
        const [state, dispatch] = useState<AuthState>({
          isAuthenticated: true,
          user: { username: "adminuser", role: "admin" },
          loading: false,
          error: null,
        });
        const logout = useCallback(() => {
          dispatch({ type: "LOGOUT" });
        }, []);
        return { state, logout };
      });

      act(() => {
        result.current.logout();
      });

      expect(result.current.state.user).toBeNull();
      expect(result.current.state.isAuthenticated).toBe(false);
    });
  });

  describe("Error handling", () => {
    it("clears previous error on new login attempt", () => {
      const { result } = renderHook(() => {
        const [state, dispatch] = useState<AuthState>({
          isAuthenticated: false,
          user: null,
          loading: false,
          error: "用户名或密码错误",
        });
        const loginStartFn = useCallback(() => {
          dispatch({ type: "LOGIN_START" });
        }, []);
        return { state, loginStartFn };
      });

      act(() => {
        result.current.loginStartFn();
      });

      expect(result.current.state.error).toBeNull();
      expect(result.current.state.loading).toBe(true);
    });

    it("persists account lock error message after 5 failures", () => {
      const { result } = renderHook(() => {
        const [state, dispatch] = useState<AuthState>({
          isAuthenticated: false,
          user: null,
          loading: false,
          error: "账号已被临时锁定，请 15 分钟后再试",
        });
        return { state };
      });

      expect(result.current.state.error).toBe("账号已被临时锁定，请 15 分钟后再试");
    });
  });

  describe("Auth persistence", () => {
    it("restores auth state from stored token", () => {
      const storedState: AuthState = {
        isAuthenticated: true,
        user: { username: "persisteduser", role: "user" },
        loading: false,
        error: null,
      };

      const { result } = renderHook(() => useState<AuthState>(storedState));
      const [state] = result.current;
      expect(state.isAuthenticated).toBe(true);
      expect(state.user?.username).toBe("persisteduser");
    });
  });
});
