import { useEffect, useState } from "react";
import { getJson } from "./api";
import { messageOf } from "./format";

const POLL_MS = 2000;

export function useHash(): string {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const onChange = () => {
      setHash(window.location.hash);
    };
    window.addEventListener("hashchange", onChange);
    return () => {
      window.removeEventListener("hashchange", onChange);
    };
  }, []);
  return hash;
}

export interface Resource<T> {
  data: T | undefined;
  error: string | undefined;
  reload: () => void;
}

// Loads a path and reloads it every couple of seconds, unless pollMs is 0.
export function useResource<T>(path: string, pollMs = POLL_MS): Resource<T> {
  const [data, setData] = useState<T>();
  const [error, setError] = useState<string>();
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let active = true;
    const load = () => {
      getJson<T>(path).then(
        (value) => {
          if (active) {
            setData(value);
            setError(undefined);
          }
        },
        (problem: unknown) => {
          if (active) {
            setError(messageOf(problem));
          }
        },
      );
    };
    load();
    const timer = pollMs > 0 ? window.setInterval(load, pollMs) : undefined;
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [path, pollMs, version]);

  return {
    data,
    error,
    reload: () => {
      setVersion((count) => count + 1);
    },
  };
}
