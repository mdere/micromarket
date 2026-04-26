async function getApiStatus(): Promise<string> {
  const baseUrl = process.env.MICROMARKET_API_BASE_URL ?? "http://localhost:8000";

  try {
    const response = await fetch(`${baseUrl}/health`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return `API unavailable (${response.status})`;
    }

    const body = (await response.json()) as { status?: string; version?: string };
    return `${body.status ?? "unknown"} / ${body.version ?? "unversioned"}`;
  } catch {
    return "API not reachable";
  }
}

export async function ApiStatus() {
  const status = await getApiStatus();

  return <p className="disclaimer">{status}</p>;
}
