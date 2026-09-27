/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  eslint: { ignoreDuringBuilds: false },
  experimental: {
    optimizePackageImports: ["lucide-react", "recharts", "date-fns", "@xyflow/react", "framer-motion"],
  },
};

export default nextConfig;
