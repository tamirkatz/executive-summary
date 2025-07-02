import React from "react";

const Header: React.FC = () => {
  return (
    <div className="relative mb-20">
      <div className="text-center pt-8">
        <h1 className="text-[56px] font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 font-['Inter'] tracking-[-2px] leading-[60px] text-center mx-auto antialiased">
          Executive Intelligence X
        </h1>
        <p className="text-gray-700 text-xl font-['Inter'] font-medium mt-6 max-w-2xl mx-auto leading-relaxed">
          "10X your strategic advantage with AI-powered competitive
          intelligence—before your competitors even know what hit them."
        </p>
      </div>
    </div>
  );
};

export default Header;
