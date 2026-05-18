const BASE_URL = "http://127.0.0.1:8000/api";

export async function apiRequest(endpoint, method = "GET", body = null) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);

  try {
    const options = {
      method,
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
    };

    if (body && method !== "GET") {
      options.body = JSON.stringify(body);
    }

    const res = await fetch(`${BASE_URL}${endpoint}`, options);
    clearTimeout(timeout);

    const contentType = res.headers.get("content-type") || "";
    let data;
    if (contentType.includes("application/json")) {
      data = await res.json();
    } else {
      data = await res.text();
    }

    if (!res.ok) {
      let message = "Request failed";
      if (typeof data === "string")  message = data;
      else if (data?.message)        message = data.message;
      else if (data?.detail)         message = data.detail;
      console.error(`❌ API Request Failed: ${message}`);
      throw new Error(message);
    }

    return data;

  } catch (error) {
    clearTimeout(timeout);
    const message = error.name === "AbortError" ? "Request timed out" : error.message;
    console.error(`❌ API Request Error: ${message}`);
    return { error: true, message };
  }
}