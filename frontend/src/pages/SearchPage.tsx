import { useEffect, useState } from "react";
import useSWR from "swr";
import { useSearchParams } from "react-router-dom";

import GoodCard from "../components/GoodCard";
import { postFetcher } from "../utils";
import type { Good } from "../types";
import PageLayout from "../components/PageLayout";

interface SearchResponse {
  goods: Good[];
}

interface SearchResquest {
  keyword: string;
}

function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [formInput, setFormInput] = useState("");
  const [keyword, setKeyword] = useState("");

  // 使用 SWR 获取数据
  const { data, error, mutate, isLoading } = useSWR<SearchResponse, Error>(
    keyword ? ['/api/good/search', keyword] : null,
    async ([url, keyword]) => postFetcher<SearchResponse>(url, {arg: { keyword: keyword }}),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      dedupingInterval: 60 * 60 * 1000 // one hour
    }
  );

  useEffect(() => {
    const query = searchParams.get("q");
    if (query?.trim()) {
      setKeyword(query);
      setFormInput(query);
      mutate();
    }
  }, []);

  // 处理搜索按钮点击事件
  const handleSearch = () => {
    if (formInput?.trim()) {
      setSearchParams({ q: formInput });
      setKeyword(formInput);
      mutate();
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
    <PageLayout>
      <div className="w-full flex justify-center">
        <img src="./logo.svg" alt="Your Image" className="max-w-full max-h-60" />
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
          Search
        </button>
      </div>

      {/* Cards */}
      <div className="flex flex-wrap justify-around p-12">
        {error && !isLoading ? (
          <div className="text-red-500">Failed to load data</div>
        ) : (!data && isLoading) ? (
          <div className="text-gray-500 mt-5">Loading...</div>
        ) : (
          goodCardList
        )}
      </div>
    </PageLayout>
  );
}

export default SearchPage;