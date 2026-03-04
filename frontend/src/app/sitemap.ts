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

export default function sitemap(): MetadataRoute.Sitemap {
  const siteOrigin = resolveSiteOrigin();

  return [
    {
      url: `${siteOrigin}/`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 1
    }
  ];
}
