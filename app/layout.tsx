import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NetShield — Topology-Aware Network Threat Detection",
  description: "AI-powered intrusion detection, dynamic trust propagation, and adaptive security decisions for heterogeneous network topologies.",
  keywords: ["network security", "threat detection", "IDS", "CICIDS2017", "machine learning"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=JetBrains+Mono:ital,wght@0,300;0,400;0,500;0,700;1,400&family=Syne:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
