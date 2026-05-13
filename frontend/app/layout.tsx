import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Requirement Plan Generator",
  description: "Generate FRDs, diagrams, and developer backlogs from raw requirements.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

