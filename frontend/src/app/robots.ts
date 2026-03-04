import type { MetadataRoute } from "next";

function resolveSiteOrigin() {
  const fallbackUrl = "http://localhost:3000";
  const configuredUrl = process.env.NEXT_PUBLIC_SITE_URL?.trim();

  if (!configuredUrl) {
    return new URL(fallbackUrl).origin;
  }

  try {
    return new URL(configuredUrl).origin;
  } catch {
    return new URL(fallbackUrl).origin;
  }
}

export default function robots(): MetadataRoute.Robots {
  const siteOrigin = resolveSiteOrigin();

  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/app", "/app/", "/auth", "/auth/"]
      }
    ],
    sitemap: [`${siteOrigin}/sitemap.xml`],
    host: siteOrigin
  };
}
