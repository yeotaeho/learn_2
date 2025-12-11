import type { NextConfig } from "next";
import { config } from "dotenv";
import { resolve } from "path";

// 루트 디렉토리의 .env 파일 로드 (www.labzang.com의 상위 디렉토리)
// process.cwd()는 www.labzang.com을 가리키므로, 상위 디렉토리로 이동
const rootEnvPath = resolve(process.cwd(), "../.env");
config({ path: rootEnvPath });

const nextConfig: NextConfig = {
  /* config options here */
  env: {
    // 루트의 .env에서 NEXT_PUBLIC_KAKAO_MAP_API_KEY를 가져옴
    NEXT_PUBLIC_KAKAO_MAP_API_KEY: process.env.NEXT_PUBLIC_KAKAO_MAP_API_KEY || "",
  },
};

export default nextConfig;
