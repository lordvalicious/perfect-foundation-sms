import { useCallback, useEffect, useState } from "react";

export function useApiList(url) {
  const [rows, setRows] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [next, setNext] = useState(null);
  const [previous, setPrevious] = useState(null);

  const load = useCallback(
    (params) => {
      return fetch(`${url}?${params.toString()}`)
        .then((response) => {
          if (!response.ok) {
            throw new Error("Failed to load data.");
          }

          return response.json();
        })
        .then((json) => {
          if (Array.isArray(json)) {
            setRows(json);
            setCount(json.length);
            setNext(null);
            setPrevious(null);
          } else {
            setRows(json.results || []);
            setCount(json.count || 0);
            setNext(json.next);
            setPrevious(json.previous);
          }
        })
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false));
    },
    [url]
  );

  const refresh = useCallback(
    (params) => {
      setLoading(true);
      setError("");
      setPage(Number(params.get("page") || 1));
      return load(params);
    },
    [load]
  );

  useEffect(() => {
    load(new URLSearchParams({ page: 1 }));
  }, [load]);

  return {
    rows,
    count,
    loading,
    error,
    page,
    next,
    previous,
    refresh,
  };
}
