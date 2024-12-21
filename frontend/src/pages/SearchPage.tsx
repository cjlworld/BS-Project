import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import ReactMarkdown from 'react-markdown';

import GoodCard from "../components/GoodCard";
import { useStreamFetcher, useStringStreamFetcher } from "../utils";
import type { Good } from "../types";
import PageLayout from "../components/PageLayout";


function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [formInput, setFormInput] = useState("");
  const [keyword, setKeyword] = useState("");

  const { data: goodsData, error: goodsError, isLoading: goodsIsLoading, trigger: goodsTrigger } = useStreamFetcher<Good>(
    '/api/good/search',
    { keyword },
  );

  const { data: aiData, trigger: aiTrigger } = useStringStreamFetcher<string>(
    '/api/good/ai',
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
      goodsTrigger();
      aiTrigger();
    }
  }, [keyword]);

  // 根据返回的数据生成产品卡片列表
  const goodCardList = goodsData?.map((good, index) => {
    // 5 的整数倍
    const total = goodsData?.length - goodsData?.length % 5;
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
        <button className="btn btn-outline mx-5" disabled={goodsIsLoading} onClick={handleSearch}>
          {goodsIsLoading ? "Loading" : "Search"}
        </button>
      </div>
        
      {
        aiData && (
          <div className="card card-compact bg-base-100 mx-auto flex justify-center mt-5 p-4">
            <div className="card-body">
              <h2 className="card-title text-base"> AI 智选 </h2>
              <div className="text-gray-500 mx-auto">
                <ReactMarkdown>{aiData}</ReactMarkdown>
                {/* {aiData} */}
              </div>
            </div>
          </div>
        )
      }

      {/* Cards */}
      <div className="w-full flex flex-col justify-center justify-items-center">
        {goodsError && !goodsIsLoading ? (
          <div className="text-red-500 mt-5 mx-auto">Failed to load data</div>
        ) : (!goodsData && goodsIsLoading) ? (
          <div className="text-gray-500 mt-5 mx-auto">Loading...</div>
        ) : (
          <>
            {goodsIsLoading && <div className="text-gray-500 mt-5 mx-auto">Loading...</div>}
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