import { HashRouter, Route, Routes } from "react-router-dom";

import SearchPage from "./pages/SearchPage";
import LoginPage from "./pages/LoginPage";
import SignUpPage from "./pages/SignUpPage";
import GoodDetailPage from "./pages/GoodDetailPage";
import SubscriptionPage from "./pages/SubscriptionPage";


function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" Component={SearchPage} />
        <Route path="/login" Component={LoginPage} />
        <Route path="/signup" Component={SignUpPage} />
        <Route path="/good-detail/:id" Component={GoodDetailPage} />
        <Route path="/subscription" Component={SubscriptionPage} />
      </Routes>
    </HashRouter>
  );
}

export default App;