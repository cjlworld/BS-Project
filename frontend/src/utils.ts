// 注意后端是 http 还是 https
// 写错了会出现 net::ERR_SSL_PROTOCOL_ERROR
const prefix: string = "http://localhost:1237";

export async function getFetcher<T>(key: string): Promise<T> {
  const resp = await fetch(prefix + key, { mode: "cors" }).then((res) =>
    res.json()
  );
  if (resp.code !== 0) {
    throw new Error(resp.message + resp.code);
  }
  return resp.data;
}

export async function postFetcher<T>(
  key: string,
  body: { arg: Record<string, unknown> | Array<unknown> }
): Promise<T> {
  const resp = await fetch(prefix + key, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body.arg),
    mode: "cors",
  }).then((res) => res.json());
  if (resp.code !== 0) {
    throw new Error(resp.message + resp.code);
  }
  return resp.data;
}
