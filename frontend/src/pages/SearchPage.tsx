import React, { useEffect, useState } from "react";
import useSWRMutation from "swr/mutation";

import GoodCard from "../components/GoodCard";
import NavBar from "../components/NavBar";
import { postFetcher } from "../utils";

import type { Good } from "../types";
import { useSearchParams } from "react-router-dom";

interface SearchResponse {
  goods: Good[];
}

interface SearchResquest {
  keyword: string;
}

function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [keyword, setKeyword] = useState("");

  // 使用 SWR 获取数据
  const { data, error, trigger, reset, isMutating } = useSWRMutation<SearchResponse, Error, string, SearchResquest>(
    '/api/good/search', 
    postFetcher
  );

  useEffect(() => {
    const query = searchParams.get("q");
    if (query?.trim()) {
      setKeyword(query);
      trigger({
        keyword: query
      });
    }
  }, []);

  // 处理搜索按钮点击事件
  const handleSearch = () => {
    if (keyword?.trim()) {
      setSearchParams({ q: keyword });
      trigger({
        keyword: keyword
      });
    } 
  };

  // 根据返回的数据生成产品卡片列表
  const goodCardList = data?.goods?.map((good, index) => {
    // 5 的整数倍
    const total = data?.goods?.length - data?.goods?.length % 5;
    if (index < total) {
      return (
        <div key={index} className="mx-1 my-2">
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
    <>
      <NavBar />
      <div className="w-full flex justify-center">
        <img src="./logo.svg" alt="Your Image" className="max-w-full max-h-60" />
      </div>

      {/* Search Bar */}
      <div className="mx-auto w-full flex justify-center mt-5">
        <input
          type="text"
          placeholder="Type here"
          className="input input-bordered w-full max-w-lg"
          value={keyword}
          onChange={(e) => {
            setKeyword(e.target.value);
          }}
        />
        <button className="btn btn-outline mx-5" onClick={handleSearch}>
          Search
        </button>
      </div>

      {/* Cards */}
      <div className="flex flex-wrap justify-around p-12">
        {error ? (
          <div className="text-red-500">Failed to load data</div>
        ) : (!data && isMutating) ? (
          <div className="text-gray-500 mt-5">Loading...</div>
        ) : (
          goodCardList
        )}
      </div>
    </>
  );
}

export default SearchPage;