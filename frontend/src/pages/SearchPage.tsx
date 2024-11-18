import ProductCard from "../components/ProductCard";
import NavBar from "../components/NavBar";

function SearchPage() {

  const productCardList = Array.from({ length: 20 }, (_, i) => i + 1).map((i) => {
    return (
      <div className="mx-5 my-5">
        <ProductCard product_id={i}></ProductCard>
      </div>
      
    );
  });

  return (
    <>
      <NavBar></NavBar>

      {/* Search Bar */}
      <div className=" mx-auto w-full flex justify-center mt-5"> 
        <input type="text" placeholder="Type here" className="input input-bordered w-full max-w-lg" />
        <button className="btn btn-outline mx-5">Search</button>
      </div>

      {/* Cards */}
      <div className="flex flex-wrap justify-around">
        {productCardList}
      </div>
    </>
  );
}

export default SearchPage;
