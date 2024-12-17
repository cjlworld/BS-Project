import { useState, useEffect } from "react";

import type { Good } from "../types";
import { postFetcher } from "../utils";

interface OnlyPostId {
  post_id: string;
}

type GoodCardProps = Good | OnlyPostId;

function GoodCard(props: GoodCardProps) {
  // 如果是 只传了 post_id，则向后端请求数据
  const { post_id } = props as OnlyPostId;

  // 判断是否只传了 post_id
  const isOnlyPostId = "post_id" in props && !("name" in props);

  // 如果是只传了 post_id，则向后端请求数据
  const [goodData, setGoodData] = useState<Good | null>(null);

  useEffect(() => {
    if (isOnlyPostId) {
      postFetcher<Good>("/api/good/detail", { arg: { post_id } })
        .then((data) => {
          setGoodData(data);
        });
    } else {
      setGoodData(props as Good);
    }
  }, [post_id, props]);

  if (!goodData) {
    return <div>Loading...</div>;
  }

  return (
    <a
      className="card card-compact bg-base-100 w-60 border transition-transform duration-300 ease-in-out transform hover:scale-105 hover:shadow-xl" 
      href={`/#/good-detail/${goodData.post_id}`}
      target="_blank"
      rel="noopener noreferrer"
    >
      <figure>
        <img
          src={goodData.img.startsWith('http') ? goodData.img : `https:${goodData.img}`}
          alt={goodData.name} 
          referrerPolicy='no-referrer'
        />
      </figure>

      <hr />
      <div className="card-body">
        <h2 className="card-title text-base line-clamp-3 min-h-[4.5em]"> { goodData.name } </h2>
        <p> { goodData.platform } </p>
        <p> ￥{ goodData.price } </p>
        <p> { goodData.time } </p>
      </div>
    </a>
  );
}

export default GoodCard;