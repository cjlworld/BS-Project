import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import GoodCard from "../components/GoodCard";
import { useStreamFetcher } from "../utils";
import type { Good } from "../types";
import PageLayout from "../components/PageLayout";


function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [formInput, setFormInput] = useState("");
  const [keyword, setKeyword] = useState("");

  const { data, error, isLoading, trigger } = useStreamFetcher<Good>(
    '/api/good/search',
    { keyword },
  );

  useEffect(() => {
    const query = searchParams.get("q");
    if (query?.trim()) {
      setKeyword(query);
      setFormInput(query);
    }
  }, []);

  // 处理搜索按钮点击事件
  const handleSearch = () => {
    if (formInput?.trim()) {
      setSearchParams({ q: formInput });
      setKeyword(formInput);
    } 
  };

  useEffect(() => {
    if (keyword.trim()) {
      trigger();
    }
  }, [keyword]);

  // 根据返回的数据生成产品卡片列表
  const goodCardList = data?.map((good, index) => {
    // 5 的整数倍
    const total = data?.length - data?.length % 5;
    if (index < total) {
      return (
        <div key={good.post_id} className="mx-1 my-2">
          <GoodCard {...good}/>
        </div>
      );
    } else {
      return (
        <></>
      );
    }
  });

  return (
    <PageLayout>
      <div className="w-full flex justify-center">
        <img src="./logo.svg" alt="logo" className="max-w-full max-h-60" />
      </div>

      {/* Search Bar */}
      <div className="mx-auto w-full flex justify-center mt-5">
        <input
          type="text"
          placeholder="Type here"
          className="input input-bordered w-full max-w-lg"
          value={formInput}
          onChange={(e) => {
            setFormInput(e.target.value);
          }}
        />
        <button className="btn btn-outline mx-5" disabled={isLoading} onClick={handleSearch}>
          {isLoading ? "Loading" : "Search"}
        </button>
      </div>

      {/* Cards */}
      <div className="w-full flex flex-col justify-center justify-items-center">
        {error && !isLoading ? (
          <div className="text-red-500 mt-5 mx-auto">Failed to load data</div>
        ) : (!data && isLoading) ? (
          <div className="text-gray-500 mt-5 mx-auto">Loading...</div>
        ) : (
          <>
            {isLoading && <div className="text-gray-500 mt-5 mx-auto">Loading...</div>}
            <div className="flex flex-wrap justify-around p-12">
              {goodCardList}
            </div>
          </>
        )}
      </div>
      
    </PageLayout>
  );
}

export default SearchPage;