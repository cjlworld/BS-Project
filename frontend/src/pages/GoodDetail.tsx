import React from "react";
import useSWR from "swr";
import { useParams } from "react-router-dom";

import { postFetcher } from "../utils";

// 假设商品信息的类型定义
interface Good {
  post_id: string;
  name: string;
  platform: string;
  price: number;
  time: string;
  img: string;
}

function ProductDetail() {
  const { id: post_id } = useParams<{ id: string }>(); // 获取路由参数

  // 使用 SWR 获取商品信息
  const { data, error, isLoading } = useSWR<Good>(
    "/api/good/detail", 
    async (key: string) => postFetcher<Good>(key, {arg: { post_id }}) // 使用柯里化封装一个 post fetcher
  );

  if (error) {
    return <div className="text-center mt-8">Failed to load product.</div>;
  }

  if (!data) {
    return <div className="text-center mt-8">Loading...</div>;
  }

  

  return (
    <div className="container mx-auto p-8">
      <div className="card lg:card-side bg-base-100 shadow-xl">
        <figure>
          <img
            src={`https:${data.img}`}
            alt={data.name}
            referrerPolicy="no-referrer"
            className="w-96 h-auto"
          />
        </figure>
        <div className="card-body">
          <h2 className="card-title text-2xl">{data.name}</h2>
          <p className="text-gray-600">{data.platform}</p>
          <p className="text-xl font-bold">￥{data.price}</p>
          <p className="text-gray-500">{data.time}</p>
          <div className="card-actions justify-end">
            <button className="btn btn-primary">Buy Now</button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProductDetail;