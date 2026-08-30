import { API_BASE } from '../config/api';

export function useApiList(url, options = {}) {
  const [rows, setRows] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [params, setParams] = useState(new URLSearchParams());

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const cleanUrl = url.replace(/^\/api\//, '');
        const fullUrl = `${API_BASE}${cleanUrl}`;
        const response = await fetch(fullUrl, {
          credentials: "include",
          ...options
        });
        const result = await readJson(response, "Failed to load data.");
        setRows(result.data || []);
        setCount(result.total || 0);
      } catch (error) {
        setError(error.message);
      }
      setLoading(false);
    };

    fetchData();
    return { rows, count, loading, error, refresh };
  }, [url, options]);

  return { rows, count, loading, error, refresh };
}