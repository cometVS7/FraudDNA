"use client";

import { useState, useEffect, useCallback } from "react";

type AsyncState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: string };

export function useAsync<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = []
): AsyncState<T> & { refetch: () => void } {
  const [state, setState] = useState<AsyncState<T>>({ status: "idle" });

  const execute = useCallback(async () => {
    setState({ status: "loading" });
    try {
      const data = await fetcher();
      setState({ status: "success", data });
    } catch (err) {
      setState({
        status: "error",
        error: err instanceof Error ? err.message : "Unknown error",
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    execute();
  }, [execute]);

  return { ...state, refetch: execute };
}
