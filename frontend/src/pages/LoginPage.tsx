import useSWRMutation from "swr/mutation"
import { useNavigate } from "react-router-dom";
import { useState } from "react";

import NavBar from "../components/NavBar";
import { postFetcher } from "../utils";

interface LoginRequest {
  email: string;
  password: string;
}

function LoginCard() {

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const navigate = useNavigate();

  const { trigger, error, isMutating } = useSWRMutation<null, Error, string, LoginRequest>(
    "/api/user/login",
    postFetcher
  )

  const handleLogin = async () => {
    await trigger({ email, password } as LoginRequest);
    if (!error) {
      navigate("/");
    }
  }

  return (
    <div className="card bg-base-100 w-96 shadow-xl">
      <div className="card-body">
        <h2 className="card-title">登录</h2>
        <div className="w-full max-w-md mx-auto">
          <label className="input input-bordered flex items-center gap-2 my-3">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 16 16"
              fill="currentColor"
              className="h-4 w-4 opacity-70">
              <path
                d="M2.5 3A1.5 1.5 0 0 0 1 4.5v.793c.026.009.051.02.076.032L7.674 8.51c.206.1.446.1.652 0l6.598-3.185A.755.755 0 0 1 15 5.293V4.5A1.5 1.5 0 0 0 13.5 3h-11Z" />
              <path
                d="M15 6.954 8.978 9.86a2.25 2.25 0 0 1-1.956 0L1 6.954V11.5A1.5 1.5 0 0 0 2.5 13h11a1.5 1.5 0 0 0 1.5-1.5V6.954Z" />
            </svg>
            <input type="text" className="grow" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label className="input input-bordered flex items-center gap-2 my-3">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 16 16"
              fill="currentColor"
              className="h-4 w-4 opacity-70">
              <path
                fillRule="evenodd"
                d="M14 6a4 4 0 0 1-4.899 3.899l-1.955 1.955a.5.5 0 0 1-.353.146H5v1.5a.5.5 0 0 1-.5.5h-2a.5.5 0 0 1-.5-.5v-2.293a.5.5 0 0 1 .146-.353l3.955-3.955A4 4 0 1 1 14 6Zm-4-2a.75.75 0 0 0 0 1.5.5.5 0 0 1 .5.5.75.75 0 0 0 1.5 0 2 2 0 0 0-2-2Z"
                clipRule="evenodd" />
            </svg>
            <input type="password" className="grow" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
        </div>
        <div className="card-actions justify-end">
          <button className="btn btn-primary" disabled={isMutating} onClick={handleLogin}>
            { isMutating ? "登录中..." : "启动！" }
          </button>
        </div>
        {error && <p className="text-red-500">登录失败！邮箱或密码错误</p>}
      </div>
    </div>
  );
};



function LoginPage() {

  return (
    <div className="flex flex-col h-screen justify-center">
      <NavBar></NavBar>
      <div className="flex justify-center my-auto">
        <LoginCard></LoginCard>
      </div>
    </div>
  );
}

export default LoginPage;
