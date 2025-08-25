// src/lib/auth/tokenStore.ts
type Listener = (token: string | null) => void;

let _token: string | null = null;
const listeners = new Set<Listener>();

export const tokenStore = {
  get(): string | null {
    return _token;
  },
  set(token: string | null) {
    _token = token;
    for (const fn of listeners) fn(_token);
  },
  subscribe(fn: Listener) {
    listeners.add(fn);
    return () => listeners.delete(fn);
  },
  clear() {
    tokenStore.set(null);
  },
};
