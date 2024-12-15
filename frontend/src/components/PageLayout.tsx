import React from "react";

import NavBar from "./NavBar";

interface PageLayoutProps {
  children: React.ReactNode;
}

function PageLayout(props: PageLayoutProps) {
  return (
    <div className="min-h-screen bg-[url('./background.png')] bg-cover bg-center bg-fixed flex flex-col">
      <NavBar></NavBar>
      {props.children}
    </div>
  );
}

export default PageLayout;