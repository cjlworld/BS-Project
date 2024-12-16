import { useNavigate } from "react-router-dom";
import { postFetcher } from "../utils";
import useSWR from "swr";
import { useAtom } from "jotai";

import { isLoginAtom } from "../store";
import { useEffect } from "react";

function NavBar() {
  const navigate = useNavigate();

  const [isLogin, setIsLogin] = useAtom(isLoginAtom);

  const { data: refreshData, error: refreshError, mutate: refreshMutate } = useSWR<{}, Error>(
    "/api/user/refresh", 
    async (key: string) => postFetcher(key, { arg: {} }),
    { dedupingInterval: 0, refreshInterval: 1000000 } // 不是幂等接口, 禁用缓存
  );

  // 由于 swr 的返回是异步的，需要使用 useEffect 来确保 atom 的值正确及时刷新
  useEffect(() => {
    if (refreshData) {
      setIsLogin(true);
    }
    if (refreshError) {
      setIsLogin(false);
    }
  }, [refreshData, refreshError]);

  useEffect(() => {
    refreshMutate();
    // console.log('isLogin', isLogin);
  }, []);

  // 处理登出
  const handleLogout = async () => {
    console.log("Logout");
    await postFetcher("/api/user/logout", { arg: {} });
    setIsLogin(false);
  };

  return (
    <div className="navbar bg-base-100">
      <div className="navbar-start">
      </div>
      <div className="navbar-center">
        <a 
          className="btn btn-ghost text-xl"
          onClick={() => navigate("/")}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          启真智选
        </a>
      </div>
      <div className="navbar-end">
        {/* <button className="btn btn-ghost text-md" onClick={() => navigate("/")}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          搜索
        </button> */}
        {
          isLogin ? (
            <>
              <button 
                className="btn btn-ghost text-md"
                onClick={() => navigate("/subscription")}>
                我的订阅
              </button>
              <button
                className="btn btn-ghost text-md"
                onClick={handleLogout}
              >
                登出
              </button>
            </>
          ) : (
            <>
              <button
                className="btn btn-ghost text-md"
                onClick={() => navigate("/login")}
              >
                登录
              </button>
              <button
                className="btn btn-ghost text-md"
                onClick={() => navigate("/signup")}
              >
                注册
              </button>
            </>
          )
        }
      </div>
    </div>
  );
}

export default NavBar;
