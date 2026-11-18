async function request(url, options = {}) {
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    credentials: "include",
  });

  const data = await res.json().catch(() => ({}));

  return {
    ok: res.ok,
    status: res.status,
    ...data,
  };
}

export const api = {
  login: (body) =>
    request("/api/login", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  register: (body) =>
    request("/api/register", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  logout: () =>
    request("/api/logout", {
      method: "POST",
    }),

  me: () => request("/api/me"),
};
