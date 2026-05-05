import type { Metadata } from "next";
import "./globals.css";
import { AppProviders } from "@/components/layout/app-providers";

export const metadata: Metadata = {
  title: "VertiOne Web",
  description: "Web console for VertiOne operations"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
