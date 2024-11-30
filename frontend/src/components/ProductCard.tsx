import { useNavigate } from "react-router-dom";

function ProductCard(props: {product_id: Number}) {
  const navigate = useNavigate();

  return (
    <div className="card card-compact bg-base-100 w-60 shadow-xl">
      <figure>
        <img
          src="https://img.daisyui.com/images/stock/photo-1606107557195-0e29a4b5b4aa.webp"
          alt="Shoes" />
      </figure>
      <div className="card-body">
        <h2 className="card-title">Shoes!</h2>
        <p>If a dog chews shoes whose shoes does he choose? product_id = {`${props.product_id}`}</p>
        <div className="card-actions justify-end">
          <button className="btn btn-primary" onClick={() => navigate(`/product-detail/${props.product_id}`)}>Buy Now</button>
        </div>
      </div>
    </div>
  );
}

export default ProductCard;