import useSWR from "swr";

import PageLayout from "../components/PageLayout";
import { postFetcher } from "../utils";
import GoodDetailCard from "../components/GoodDetailCard";

type SubscriptionGetResponse = string[]

function SubscriptionPage() {
  const { data, error } = useSWR<SubscriptionGetResponse, Error>(
    "/api/subscription/get", 
    async (key: string) => postFetcher<SubscriptionGetResponse>(key, { arg: {} }),
  );

  const goodDetailList = data?.map((good_post_id) => (
    <div className="mt-8">
      <GoodDetailCard post_id={good_post_id} />
    </div>
  ));

  console.log('data', data);
  console.log('error', error);

  return (
    <PageLayout>
      <div className="container mx-auto p-8">
        <div className="mt-8">
          <h3 className="text-xl font-bold mb-4">我的收藏</h3>
          {goodDetailList}
        </div>
      </div>
    </PageLayout>
  );
}

export default SubscriptionPage;
