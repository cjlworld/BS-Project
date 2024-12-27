import useSWR from "swr";
import { useParams } from "react-router-dom";
import { Table } from 'antd';
import { Line } from '@ant-design/plots';

import { postFetcher } from "../utils";
import PageLayout from "../components/PageLayout";
// import GoodCard from "../components/GoodCard";
import GoodDetailCard from "../components/GoodDetailCard";

interface HistoryData {
  post_id: string;
  time: string;
  price: number;
  name: string;
}

type GoodHistoryResponse = HistoryData[];

function GoodDetailPage() {
  const { id: post_id } = useParams<{ id: string }>(); // 获取路由参数

  if (!post_id) {
    return <div>Invalid post ID</div>;
  }

  // 使用 SWR 获取历史信息
  const { data: historyData, error: historyError, isLoading: historyIsLoading } = useSWR<GoodHistoryResponse>(
    ["/api/good/history", post_id],
    async ([url, post_id]) => postFetcher<GoodHistoryResponse>(url, {arg: { post_id: post_id }})
  );

  // 处理加载状态
  if (historyIsLoading) {
    return <div className="text-center mt-8">Loading...</div>;
  }

  // 处理错误状态
  if (historyError) {
    return <div className="text-center mt-8">Failed to load data.</div>;
  }

  // 如果没有数据，返回提示
  if (!historyData) {
    return <div className="text-center mt-8">No data found.</div>;
  }

  // 定义表格列
  const columns = [
    { title: '价格', dataIndex: 'price', key: 'price' },
    { title: '时间', dataIndex: 'time', key: 'time' },
    { title: '商品（点击跳转）', dataIndex: 'post_id', key: 'post_id' },
  ];

  const tableData = Array.from(historyData).reverse().map(item => ({
    price: item.price,
    time: item.time,
    key: `${item.time} ${item.price}`,
    post_id: (
      <a href={`/#/good-detail/${item.post_id}`}>{item.name}</a>
    )
  }));

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
  };

  // const uniquePostIds = Array.from(new Set(historyData.map((item) => item.post_id)));
  // const relatedGoodList = uniquePostIds.map((postId) => ( 
  //   <GoodCard key={postId} post_id={postId} />
  // ));

  

  return (
    <PageLayout>
      <div className="container mx-auto p-8">
        {/* 商品详情 */}
        <GoodDetailCard post_id={post_id} />

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
          <Table dataSource={tableData} columns={columns} rowKey="key" />
        </div>

        {/* 相关商品 */}
        {/* <div className="mt-8">
          <h3 className="text-xl font-bold mb-4">相关商品</h3>
          
        </div> */}

      </div>
    </PageLayout>
  );
}

export default GoodDetailPage;