import { useEffect, useState, useRef } from "react";

// 注意后端是 http 还是 https
// 写错了会出现 net::ERR_SSL_PROTOCOL_ERROR
const prefix: string = "http://localhost:8000";

export async function getFetcher<T>(key: string): Promise<T> {
  const resp = await fetch(prefix + key, {
    mode: "cors", // 跨域请求
    credentials: "include", // 允许跨域携带 cookie
  }).then((res) => res.json());
  if (resp.code !== 0) {
    throw new Error(`${resp.code}, ${resp.msg}`);
  }
  return resp.data;
}

export async function postFetcher<T>(
  key: string,
  body: { arg: unknown }
): Promise<T> {
  const resp = await fetch(prefix + key, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body.arg),
    mode: "cors", // 跨域请求
    credentials: "include", // 允许跨域携带 cookie
  }).then((res) => res.json());
  if (resp.code !== 0) {
    throw new Error(`${resp.code}, ${resp.msg}`);
  }
  return resp.data;
}

function parseJsonLines<T>(jsonl: string): T[] {
  const lines = jsonl.split("\n"); // 按换行符分割
  const parsedData: T[] = [];

  for (const line of lines) {
    if (line.trim()) {
      // 忽略空行
      try {
        const obj = JSON.parse(line) as T[]; // 解析每行的 JSON 数据
        parsedData.push(...obj);
      } catch (e) {
        console.error("Failed to parse JSON line:", line, e);
      }
    }
  }

  return parsedData;
}

export function useStreamFetcher<T>(key: string, body: unknown) {
  const [data, setData] = useState<T[] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const errorRef = useRef<Error | null>(null);
  const dataRef = useRef<T[] | null>(null);

  async function fetchStream() {
    if (isLoading) return;
    setIsLoading(true);
    errorRef.current = null;
    dataRef.current = null;

    try {
      const response = await fetch(prefix + key, {
        mode: "cors",
        credentials: "include",
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error("Response body is empty!");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let result = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }
        result += decoder.decode(value, { stream: true });

        // 逐步解析数据并更新 UI
        try {
          const parsedData = parseJsonLines<T>(result);
          dataRef.current = parsedData;
          setData(dataRef.current);
        } catch (e) {
          // 如果数据不完整，继续读取
        }
      }
    } catch (e) {
      errorRef.current = e as Error;
    } finally {
      setIsLoading(false);
    }
  }

  return {
    data,
    error: errorRef.current,
    isLoading,
    trigger: fetchStream,
  };
}
