import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { basicAuthHeader } from "../lib/basicAuth";

const STORAGE_BASIC = "dashboard_basic";
const STORAGE_USER = "dashboard_user";

type AuthState = {
  username: string;
  authorization: string | null;
};

type AuthContextValue = AuthState & {
  login: (username: string, password: string) => void;
  logout: () => void;
  /** Fresh Basic header for destructive actions (re-enter password). */
  oneOffAuth: (password: string) => string;
  isLoggedIn: boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function readStored(): AuthState {
  try {
    const authorization = sessionStorage.getItem(STORAGE_BASIC);
    const username = sessionStorage.getItem(STORAGE_USER) ?? "";
    return { username, authorization };
  } catch {
    return { username: "", authorization: null };
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(() =>
    typeof window !== "undefined" ? readStored() : { username: "", authorization: null },
  );

  const login = useCallback((username: string, password: string) => {
    const authorization = basicAuthHeader(username, password);
    try {
      sessionStorage.setItem(STORAGE_BASIC, authorization);
      sessionStorage.setItem(STORAGE_USER, username);
    } catch {
      /* ignore */
    }
    setState({ username, authorization });
  }, []);

  const logout = useCallback(() => {
    try {
      sessionStorage.removeItem(STORAGE_BASIC);
      sessionStorage.removeItem(STORAGE_USER);
    } catch {
      /* ignore */
    }
    setState({ username: "", authorization: null });
  }, []);

  const oneOffAuth = useCallback(
    (password: string) => {
      const user = state.username || readStored().username;
      return basicAuthHeader(user, password);
    },
    [state.username],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      login,
      logout,
      oneOffAuth,
      isLoggedIn: Boolean(state.authorization),
    }),
    [state, login, logout, oneOffAuth],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
