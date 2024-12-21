import useSWR from "swr";

import { Good } from "../types";
import { postFetcher } from "../utils";

interface SubscriptionCheckResponse {
  is_subscribed: boolean;
}


interface SubscriptionButtonProps {
  post_id: string;
}

function SubscriptionButton(props: SubscriptionButtonProps) {
  // 订阅 / 取消订阅
  const { data, error, mutate } = useSWR<SubscriptionCheckResponse, Error>(
    ["/api/subscription/check", props.post_id],
    async ([url, post_id]) =>
      postFetcher<SubscriptionCheckResponse>(url, { arg: { good_post_id: post_id } }),
  );

  if (error) {
    return <></>;
  }
  if (!data) {
    return <></>;
  }

  const handleSubscriptionAdd = async () => {
    await postFetcher<{}>("/api/subscription/add", { arg: { good_post_id: props.post_id } });
    mutate();
  };
  const handleSubscriptionCancel = async () => {
    await postFetcher<{}>("/api/subscription/cancel", { arg: { good_post_id: props.post_id } });
    mutate();
  };

  return (
    data.is_subscribed ? (
      <button
        className="btn btn-primary"
        onClick={handleSubscriptionCancel}
      >
        取消订阅
      </button>
    ) : (
      <button
        className="btn btn-primary"
        onClick={handleSubscriptionAdd}
      >
        去订阅
      </button>
    )
  )
}


interface GoodDetailCardProps {
  post_id: string;
}

//  显示单个商品的详细信息
function GoodDetailCard(props: GoodDetailCardProps) {

  console.log("GoodDetailCard props: ", props)
  
  // 使用 SWR 获取商品信息
  const { data: detailData, error: detailError, isLoading: detailIsLoading } = useSWR<Good>(
    ["/api/good/detail", props.post_id], 
    async ([url, post_id]) => 
      postFetcher<Good>(url, {arg: { post_id }}) // 封装一个 post fetcher
  );

  // 处理加载状态
  if (detailIsLoading) {
    return <div className="text-center mt-8">Loading...</div>;
  }

  // 处理错误状态
  if (detailError) {
    return <div className="text-center mt-8">Failed to load data.</div>;
  }

  // 如果没有数据，返回提示
  if (!detailData) {
    return <div className="text-center mt-8">No data found.</div>;
  }

  return (
    <div className="card lg:card-side bg-base-100 shadow-xl">
      <figure>
        <img
          src={`https:${detailData.img}`}
          alt={detailData.name}
          referrerPolicy="no-referrer"
          className="w-96 h-auto"
        />
      </figure>
      <div className="card-body">
        <h2 className="card-title text-2xl">{detailData.name}</h2>
        <p className="text-gray-600">{detailData.platform}</p>
        <p className="text-xl font-bold">￥{detailData.price}</p>
        <p className="text-gray-500">{detailData.time}</p>
        <div className="card-actions justify-end">
          <SubscriptionButton post_id={detailData.post_id}></SubscriptionButton>
          {/* 如果当前不是在 /#/good-detail/ 页面，则显示返回按钮 */
            (!window.location.hash.startsWith("#/good-detail")) && (
              <a
                href={`/#/good-detail/${detailData.post_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary"
              >
                商品详情页
              </a>
            )
          }
          <a
            href={detailData.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-primary"
          >
            链接直达
          </a>
        </div>
      </div>
    </div>
  );
}

export default GoodDetailCard;
