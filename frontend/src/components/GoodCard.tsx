import { useNavigate } from "react-router-dom";

import type { Good } from "../types";

type GoodCardProps = Good;

function GoodCard(props: GoodCardProps) {
  return (
    <a
      className="card card-compact bg-base-100 w-60 border transition-transform duration-300 ease-in-out transform hover:scale-105 hover:shadow-xl" 
      href={`/#/good-detail/${props.post_id}`}
      target="_blank"
      rel="noopener noreferrer"
    >
      <figure>
        <img
          src={`https:${props.img}`}
          alt={props.name} 
          referrerPolicy='no-referrer'
        />
      </figure>

      <hr />
      <div className="card-body">
        <h2 className="card-title text-base"> { props.name } </h2>
        <p> { props.platform } </p>
        <p> ￥{ props.price } </p>
        <p> { props.time } </p>
      </div>
    </a>
  );
}

export default GoodCard;