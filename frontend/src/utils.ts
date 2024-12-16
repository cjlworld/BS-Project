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
