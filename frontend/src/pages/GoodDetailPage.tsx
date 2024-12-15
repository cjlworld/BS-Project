import React from "react";
import useSWR from "swr";
import { useParams } from "react-router-dom";
import { Table } from 'antd';
import { Line } from '@ant-design/plots';

import { postFetcher } from "../utils";
import PageLayout from "../components/PageLayout";

// 假设商品信息的类型定义
interface Good {
  post_id: string;
  name: string;
  url: string;
  platform: string;
  price: number;
  time: string;
  img: string;
}

interface HistoryData {
  post_id: string;
  time: string;
  price: number;
}

type GoodHistoryResponse = HistoryData[];

function GoodDetail() {
  const { id: post_id } = useParams<{ id: string }>(); // 获取路由参数

  // 使用 SWR 获取商品信息
  const { data: detailData, error: detailError, isLoading: detailIsLoading } = useSWR<Good>(
    "/api/good/detail", 
    async (key: string) => postFetcher<Good>(key, {arg: { post_id }}) // 使用柯里化封装一个 post fetcher
  );

  // 使用 SWR 获取历史信息
  const { data: historyData, error: historyError, isLoading: historyIsLoading } = useSWR<GoodHistoryResponse>(
    "/api/good/history", 
    async (key: string) => postFetcher<GoodHistoryResponse>(key, {arg: { post_id }})
  );

  // 处理加载状态
  if (detailIsLoading || historyIsLoading) {
    return <div className="text-center mt-8">Loading...</div>;
  }

  // 处理错误状态
  if (detailError || historyError) {
    return <div className="text-center mt-8">Failed to load data.</div>;
  }

  // 如果没有数据，返回提示
  if (!detailData || !historyData) {
    return <div className="text-center mt-8">No data found.</div>;
  }

  // 定义表格列
  const columns = [
    { title: '价格', dataIndex: 'price', key: 'price' },
    { title: '时间', dataIndex: 'time', key: 'time' },
    { title: '商品编号', dataIndex: 'post_id', key: 'post_id' },
  ];

  // 处理历史数据，转换为折线图所需格式
  const chartData = historyData.map(item => ({
    time: item.time,
    price: item.price,
  }));

  // 配置折线图
  const chartConfig = {
    data: chartData,
    xField: 'time',
    yField: 'price',
    xAxis: {
      type: 'time',
      title: {
        text: 'Time',
        position: 'end',
      },
    },
    yAxis: {
      title: {
        text: 'Price',
        position: 'end',
      },
    },
    point: {
      size: 5,
      shape: 'circle',
    },
    tooltip: {
      showMarkers: true,
      formatter: (datum: HistoryData) => {
        return { name: 'Price', value: `￥${datum.price}` };
      },
    },
    theme: {
      background: 'white', // 设置背景颜色为白色
    },
  };

  return (
    <PageLayout>
      <div className="container mx-auto p-8">
        <div className="card lg:card-side bg-base-100 shadow-xl">
          <figure>
            <img
              src={`https:${detailData.img}`}
              alt={detailData.name}
              referrerPolicy="no-referrer"
              className="w-96 h-auto"
            />
          </figure>
          <div className="card-body">
            <h2 className="card-title text-2xl">{detailData.name}</h2>
            <p className="text-gray-600">{detailData.platform}</p>
            <p className="text-xl font-bold">￥{detailData.price}</p>
            <p className="text-gray-500">{detailData.time}</p>
            <div className="card-actions justify-end">
              <a href={detailData.url} target="_blank" rel="noopener noreferrer" className="btn btn-primary">链接直达</a>
            </div>
          </div>
        </div>

        {/* 折线图 */}

        <div className="mt-8">
          <h3 className="text-xl font-bold mb-4">历史价格折线图</h3>
          <div className="card bg-base-100 shadow-xl">
            <div className="card-body">
              <Line {...chartConfig} />
            </div>
          </div>
        </div>

        {/* 历史价格表格 */}
        <div className="mt-8">
          <h3 className="text-xl font-bold mb-4">历史价格</h3>
          <Table dataSource={historyData} columns={columns} rowKey="time" />
        </div>

      </div>
    </PageLayout>
  );
}

export default GoodDetail;