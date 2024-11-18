import { useParams } from "react-router-dom";

function ProductDetail() {
  const params = useParams();

  return (
    <>
      {params.id}
    </>
  );
}

export default ProductDetail;