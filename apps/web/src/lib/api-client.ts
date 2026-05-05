import axios from "axios";
import { firebaseAuth } from "@/lib/firebase";

const allowedApiPrefixes = ["/api/web/"];

function assertAllowedApiPath(path: string) {
  const isAbsolute = /^https?:\/\//i.test(path);
  if (isAbsolute) {
    throw new Error("Use relative API paths so VertiOne Web can enforce API boundaries.");
  }

  const isAllowed = allowedApiPrefixes.some((prefix) => path.startsWith(prefix));
  if (!isAllowed) {
    throw new Error(
      `Blocked API path "${path}". VertiOne Web must use /api/web/* or explicitly approved protected core endpoints.`
    );
  }
}

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL,
  headers: {
    "Content-Type": "application/json"
  }
});

apiClient.interceptors.request.use(async (config) => {
  const path = config.url || "";
  assertAllowedApiPath(path);

  const token = await firebaseAuth.currentUser?.getIdToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});
